import os
import psycopg2
import sys
import time
from contextlib import contextmanager
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from postgres_to_es import logger, settings
from postgres_to_es.add_es_schemas import add_es_index, check_es_index
from postgres_to_es.loaders import PostgresLoader
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
    postgres_loader = PostgresLoader(pg_connect)
    count = 0
    data_for_save = postgres_loader.load_movie_data()
    for data in data_for_save:
        saved = postgres_loader.save_data(data=data,
                                          es_index_name='movies')
        count += len(saved)
    postgres_loader.watcher.finish()
    logger.info("Проиндексировано %s фильмов.", count)


if __name__ == '__main__':
    if not check_es_index('movies'):
        add_es_index('movies', f'{settings.es_schemas_dir}movies.json')

    with (connect_to_postgress(settings.dsl) as pg_conn):
        while True:
            load_from_postgres(pg_conn)
            time.sleep(10)
