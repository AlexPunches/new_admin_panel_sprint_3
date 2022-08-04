import logging
import os
import psycopg2
import sqlite3
import sys
from contextlib import contextmanager
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))))
sys.path.append(BASE_DIR)
from etl_services.sqlite_to_postgres.loaders import (ForeignKeyError,
                                                     LoadDataError,
                                                     PostgresSaver,
                                                     SQLiteLoader)
from example import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dsl = {
    'dbname':    os.environ.get('POSTGRES_DB'),
    'user':      os.environ.get('POSTGRES_USER'),
    'password':  os.environ.get('POSTGRES_PASSWORD'),
    'host':      os.environ.get('DB_HOST', '127.0.0.1'),
    'port':      os.environ.get('DB_PORT', 5432),
}


@contextmanager
def conn_context_sqlite3(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def load_from_sqlite(sl_connect: sqlite3.Connection, pg_connect: _connection):
    """Основной метод загрузки данных из SQLite в Postgres."""
    postgres_saver = PostgresSaver(pg_connect)
    sqlite_loader = SQLiteLoader(sl_connect)

    data_tables = sqlite_loader.get_tables()
    while len(data_tables) > 0:
        table = data_tables.pop(0)
        sqlite_loader.last_id = None
        count = 0
        try:
            data_for_save = sqlite_loader.load_data(table=table)
            for data in data_for_save:
                postgres_saver.save_data(data, table)
                count += len(data)

        except ForeignKeyError as e:
            logger.warning(e)
            data_tables.append(table)
        except LoadDataError as e:
            logger.warning(e)
        else:
            logger.info("Table <{}> finished. "
                        "Processed {} rows.".format(table, count))


if __name__ == '__main__':
    with (
        conn_context_sqlite3(settings.SQLITE3_PATH) as sqlite_conn,
        psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn
    ):
        load_from_sqlite(sqlite_conn, pg_conn)
