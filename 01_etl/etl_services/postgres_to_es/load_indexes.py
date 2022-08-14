import os
import psycopg2
import sys
import time
from contextlib import contextmanager
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from postgres_to_es import logger, settings
from postgres_to_es.add_es_schemas import add_es_index, check_es_index
from postgres_to_es.loaders import ElasticLoader, PostgresExtracter
from postgres_to_es.services import ElasticInsertError, backoff


@backoff(psycopg2.OperationalError, Exception, logger=logger)
@contextmanager
def connect_to_postgress(connect_params: dict):
    conn = None
    try:
        conn = psycopg2.connect(**connect_params, cursor_factory=DictCursor)
        yield conn
    finally:
        if conn is not None:
            conn.close()


@backoff(ElasticInsertError, logger=logger)
def load_from_postgres(pg_connect: _connection) -> None:
    """Основной метод загрузки данных из Postgres в Elasticsearch."""
    pg_extracter = PostgresExtracter(pg_connect)
    data_for_save = pg_extracter.extract_movie_data()
    loaded_count = ElasticLoader.save_data(data=data_for_save,
                                             es_index_name='movies')
    logger.info("Проиндексировано %s фильмов.", loaded_count)
    # todo: передать ответственность на класс про Watcher
    pg_extracter.es_state.finish()


if __name__ == '__main__':
    es_index_name = 'movies'
    if not check_es_index(es_index_name):
        add_es_index(es_index_name, f'{settings.es_schemas_dir}/movies.json')

    with (connect_to_postgress(settings.dsl) as pg_conn):
        while True:
            load_from_postgres(pg_conn)
            time.sleep(5)
