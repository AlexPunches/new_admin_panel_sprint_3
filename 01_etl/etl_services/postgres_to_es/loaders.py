import json
import more_itertools
from psycopg2.extras import DictRow
from typing import Generator

import requests

from postgres_to_es import DbConnect, settings
from postgres_to_es.data_scheme import MovieEsModel
from postgres_to_es.elastic_index_state import (ElasticIndexState,
                                                ElasticIndexStateError,
                                                Tracked)
from postgres_to_es.services import ElasticInsertError
from postgres_to_es.sqls.film_work_2_es_sql import film_work_2_es as fw2es


class PostgresExtracter(DbConnect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_watcher()

    def extract_movie_data(self) -> Generator[DictRow, None, None]:
        """Получить данные обновленных фильмов."""
        was_lasts = [
            self.es_state.were_lasts[Tracked.FILM_WORK],
            self.es_state.were_lasts[Tracked.GENRE],
            self.es_state.were_lasts[Tracked.PERSON],
        ]
        self.cursor.execute(fw2es, was_lasts)

        while fetched := self.cursor.fetchmany(settings.bunch_extract):
            yield from fetched

    def set_watcher(self):
        try:
            self.es_state = ElasticIndexState(self.connection)
        except Exception as e:
            raise ElasticIndexStateError() from e


class ElasticLoader:
    @classmethod
    def save_data(cls,
                  data: Generator[DictRow, None, None],
                  es_index_name: str,
                  ) -> int:
        """Записать данные в Elastic."""
        count = 0
        headers = {'Content-Type': 'application/x-ndjson'}
        for items in more_itertools.ichunked(data, settings.bunch_es_load):
            bulk_items = ''.join([
                cls._make_es_item_for_bulk(item, es_index_name)
                for item in items
            ])

            try:
                r = requests.put(f'{settings.es_base_url}/_bulk',
                                 headers=headers,
                                 data=bulk_items,
                                 )
            except requests.exceptions.ConnectionError as e:
                raise ElasticInsertError() from e
            if r.status_code == 200:
                if r.json().get('items') is not None:
                    count += len(r.json().get('items'))
            else:
                raise ElasticInsertError("Can't insert data into Elastic. "
                                         "Status_code: %s ", r.status_code)
        return count

    @staticmethod
    def _make_es_item_for_bulk(row: DictRow, es_index_name: str) -> str:
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
