import logging
import os
import psycopg2
import sys
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from time import sleep

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
sys.path.append(BASE_DIR)
from etl_services.postgres_to_es.loaders import PostgresLoader  # noqa: E402

#
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dsl = {
    'dbname':    os.environ.get('POSTGRES_DB'),
    'user':      os.environ.get('POSTGRES_USER'),
    'password':  os.environ.get('POSTGRES_PASSWORD'),
    'host':      os.environ.get('DB_HOST', '127.0.0.1'),
    'port':      os.environ.get('DB_PORT', 5432),
}


def load_from_postgres(pg_connect: _connection):
    """Основной метод загрузки данных из Postgres в Elasticsearch."""
    postgres_loader = PostgresLoader(pg_connect)
    data_for_save = postgres_loader.load_data()
    for data in data_for_save:
        print(postgres_loader.save_data(data))
        sleep(1.5)


if __name__ == '__main__':
    with (psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn):
        load_from_postgres(pg_conn)
