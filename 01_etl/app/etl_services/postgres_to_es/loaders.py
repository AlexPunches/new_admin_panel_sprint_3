import json
import logging
from datetime import datetime
from uuid import UUID

import requests

from etl_services.postgres_to_es import DbConnect
from etl_services.postgres_to_es.data_scheme import MovieEsModel
from etl_services.postgres_to_es.services import ElasticInsertError
from etl_services.postgres_to_es.watcher import Watcher
from example import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresLoader(DbConnect):
    def __init__(self, *args, **kwargs):
        super(PostgresLoader, self).__init__(*args, **kwargs)
        self.watcher = Watcher(self.connection)

    def load_movie_data(self):
        """Получить данные обновленных фильмов."""
        with open(f'{settings.ES_SCHEMAS_DIR}film_work_to_es.sql', 'r') as sql:
            stmt = sql.read()
        was_lasts = [
            self.watcher.were_lasts['film_work'] or datetime.fromtimestamp(0),
            self.watcher.were_lasts['genre'] or datetime.fromtimestamp(0),
            self.watcher.were_lasts['person'] or datetime.fromtimestamp(0),
        ]
        self.cursor.execute(stmt, was_lasts)

        while True:
            fetched = self.cursor.fetchmany(settings.BUNCH_ES)
            if len(fetched) < 1:
                return None
            yield fetched

    def save_data(self, data: list, es_index_name: str) -> list[UUID]:
        """Записать данные в Elastic."""
        if len(data) < 1:
            return None
        headers = {'Content-Type': 'application/x-ndjson'}
        bulk_items = ''
        for item in data:
            bulk_items += self.make_es_item_for_bulk(item, es_index_name)

        try:
            r = requests.put(f'{settings.ES_BASE_URL}/_bulk',
                             headers=headers,
                             data=bulk_items,
                             )
        except requests.exceptions.ConnectionError as e:
            raise ElasticInsertError(e)
        if r.status_code == 200:
            return r.json().get('items')
        raise ElasticInsertError(r.json())

    @staticmethod
    def make_es_item_for_bulk(row: dict, es_index_name: str):
        es_index = {'_index': es_index_name, '_id': row['id']}
        es_item = json.dumps({'index': es_index}) + '\n'

        movie_obj = MovieEsModel.parse_obj(row)
        es_item += movie_obj.json() + '\n'
        return es_item
