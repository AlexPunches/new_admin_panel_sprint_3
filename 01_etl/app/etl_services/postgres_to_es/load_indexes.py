import logging
import os
import psycopg2
import sys
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
sys.path.append(BASE_DIR)
from etl_services.postgres_to_es.loaders import PostgresLoader
from etl_services.postgres_to_es.services import ElasticInsertError, backoff

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dsl = {
    'dbname':    os.environ.get('POSTGRES_DB'),
    'user':      os.environ.get('POSTGRES_USER'),
    'password':  os.environ.get('POSTGRES_PASSWORD'),
    'host':      os.environ.get('DB_HOST', '127.0.0.1'),
    'port':      os.environ.get('DB_PORT', 5432),
}


@backoff(psycopg2.OperationalError, Exception, logger=logger)
def connect_to_postgress(connect_params):
    return psycopg2.connect(**connect_params, cursor_factory=DictCursor)


@backoff(ElasticInsertError, logger=logger)
def load_from_postgres(pg_connect: _connection):
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
    with (connect_to_postgress(dsl) as pg_conn):
        load_from_postgres(pg_conn)
