import json
from datetime import datetime
from psycopg2.extras import DictRow
from uuid import UUID

import requests

from postgres_to_es import DbConnect, settings
from postgres_to_es.data_scheme import MovieEsModel
from postgres_to_es.services import ElasticInsertError
from postgres_to_es.watcher import Watcher, WatcherError


class PostgresLoader(DbConnect):
    def __init__(self, *args, **kwargs):
        super(PostgresLoader, self).__init__(*args, **kwargs)
        self.set_watcher()

    def load_movie_data(self) -> list[DictRow]:
        """Получить данные обновленных фильмов."""
        with open(f'{settings.es_schemas_dir}/film_work_2_es.sql', 'r') as sql:
            stmt = sql.read()
        was_lasts = [
            self.watcher.were_lasts['film_work'] or datetime.fromtimestamp(0),
            self.watcher.were_lasts['genre'] or datetime.fromtimestamp(0),
            self.watcher.were_lasts['person'] or datetime.fromtimestamp(0),
        ]
        self.cursor.execute(stmt, was_lasts)

        while fetched := self.cursor.fetchmany(settings.bunch_es):
            yield fetched

    def save_data(self,
                  data: list[DictRow],
                  es_index_name: str,
                  ) -> list[UUID] | None:
        """Записать данные в Elastic."""
        if len(data) < 1:
            return None
        headers = {'Content-Type': 'application/x-ndjson'}
        bulk_items = ''
        for item in data:
            bulk_items += self.make_es_item_for_bulk(item, es_index_name)

        try:
            r = requests.put(f'{settings.es_base_url}/_bulk',
                             headers=headers,
                             data=bulk_items,
                             )
        except requests.exceptions.ConnectionError as e:
            raise ElasticInsertError(e)
        if r.status_code == 200:
            return [movie['index']['_id'] for movie in r.json().get('items')]
        raise ElasticInsertError(r.json())

    @staticmethod
    def make_es_item_for_bulk(row: DictRow, es_index_name: str) -> str:
        """
        Сделать пару строк[json-объектов] для Bulk-запроса в Elasticsearch
        :param row: DictRow из постгреса
        :param es_index_name: str, название индекса
        :return: str, пара json-объектов в виде строк,
            вторая строка - это MovieEsModel,
            пример:
            {"index": {"_index": "es_index_name", "_id": "my_id"}}
            {"field1": "1", "field2": "2"}
        PS
        перенос строки "\n" должен быть у каждой, даже самой последней.
        """
        es_index = {'_index': es_index_name, '_id': row['id']}
        es_item = json.dumps({'index': es_index}) + '\n'

        movie_obj = MovieEsModel.parse_obj(row)
        es_item += movie_obj.json() + '\n'
        return es_item

    def set_watcher(self):
        try:
            self.watcher = Watcher(self.connection)
        except Exception as e:
            raise WatcherError(e)
