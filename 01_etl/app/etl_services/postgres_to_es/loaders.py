import json
import logging
from datetime import datetime

import requests

from etl_services.postgres_to_es.data_scheme import MovieEsModel
from example import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresLoader:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()

    def load_data(self, timestamp: datetime = None):
        if not timestamp:
            timestamp = datetime.fromtimestamp(0)
        stmt = """
SELECT
    fw.id,
    fw.title,
    fw.description,
    fw.rating,
    fw.type,
    fw.creation_date as created,
    fw.updated_at as modified,
    array_agg(DISTINCT g.name) as genre,
    array_agg(DISTINCT p.full_name) FILTER(
        WHERE p.id is not null AND pfw.role = 'actor'
    ) as actors_names,
    array_agg(DISTINCT p.full_name) FILTER(
        WHERE p.id is not null AND pfw.role = 'writer'
    ) as writers_names,

    COALESCE (
            json_agg(DISTINCT p.full_name) FILTER(
                WHERE p.id is not null AND pfw.role = 'director'
                ),
            '[]'
        ) as director,
    COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'name', p.full_name
                )
            ) FILTER (WHERE p.id is not null AND pfw.role = 'director'),
            '[]'
        ) as directors,
    COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'name', p.full_name
                )
            ) FILTER (WHERE p.id is not null AND pfw.role = 'actor'),
            '[]'
        ) as actors,
    COALESCE (
            json_agg(
                DISTINCT jsonb_build_object(
                    'id', p.id,
                    'name', p.full_name
                )
            ) FILTER (WHERE p.id is not null AND pfw.role = 'writer'),
            '[]'
        ) as writers

FROM content.film_work fw
LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
LEFT JOIN content.person p ON p.id = pfw.person_id
LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
LEFT JOIN content.genre g ON g.id = gfw.genre_id
WHERE fw.updated_at > %s
GROUP BY fw.id
ORDER BY fw.updated_at
;
"""
        self.cursor.execute(stmt, [timestamp])

        while True:
            fetched = self.cursor.fetchmany(settings.BUNCH_ES)
            if len(fetched) < 1:
                return None
            yield fetched

    def make_es_item_for_bulk(self, row: dict):
        es_index_name = row.get('es_index', 'movies')

        es_index = {'_index': es_index_name, '_id': row['id']}
        es_item = json.dumps({'index': es_index}) + '\n'

        movie_obj = MovieEsModel.parse_obj(row)
        es_item += movie_obj.json() + '\n'
        return es_item

    def save_data(self, data: list):
        if len(data) < 1:
            return None
        headers = {'Content-Type': 'application/x-ndjson'}
        last_modified = None
        bulk_items = ''
        for movie in data:
            bulk_items += self.make_es_item_for_bulk(movie)
            last_modified = movie['modified']

        r = requests.put(f'{settings.ES_BASE_URL}/_bulk',
                         headers=headers,
                         data=bulk_items,
                         )
        self.set_last_modified_movie_date(last_modified)
        return r.json()

    def set_last_modified_movie_date(self, last_modified: datetime):
        pass


#  TODO
# хранить состояние в БД
# отказоустойчивость, backoff
