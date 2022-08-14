import more_itertools
import psycopg2
import sqlite3

from sqlite_to_postgres import logger, settings
from sqlite_to_postgres.data_classes import DATACLASSES_MAP


class LoadDataError(Exception):
    ...


class ForeignKeyError(Exception):
    ...


class DbConnect:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()


class SQLiteLoader(DbConnect):
    table: str | None
    last_id: str | None = None

    def load_data(self, table: str) -> list:
        self.table = table
        raw_data = self.load_data_from_table()
        for rows in raw_data:
            if rows:
                yield self.transform_data(rows)

    def load_data_from_table(self) -> sqlite3.Row:
        stmt = "SELECT * FROM {} ;".format(self.table)
        self.cursor.execute(stmt)

        while True:
            fetched = self.cursor.fetchmany(settings.bunch_extract)
            if len(fetched) < 1:
                return None
            yield fetched

    def transform_data(self, data: list[sqlite3.Row]) -> list:
        """Сделать список объектов датакласса."""
        dt_class = DATACLASSES_MAP.get(self.table)
        if dt_class is None:
            raise LoadDataError('Warning: unknown table <{}>. '
                                'Need a dataclass.'.format(self.table))
        return [dt_class(**row) for row in data]

    def get_tables(self, name_table: str | None = None) -> list[str]:
        """Получить список таблиц, из которых берем данные."""
        substitute = []
        stmt = "SELECT name FROM sqlite_master WHERE type='table' "
        if name_table:
            stmt += " AND name = ?"
            substitute.append(name_table)
        stmt += ";"
        self.cursor.execute(stmt, substitute)
        tables = self.cursor.fetchall()
        if len(tables) < 1:
            raise LoadDataError('Error: Tables not found in Database')
        return [table['name'] for table in tables]


class PostgresSaver(DbConnect):
    def save_data(self, data, table) -> None:
        dt_class = DATACLASSES_MAP.get(table)
        if dt_class is None:
            raise LoadDataError('Warning: unknown table <{}>. '
                                'Need a dataclass.'.format(table))
        columns = dt_class.get_fields()
        pk = self.get_pk_table(table)
        updating_columns = columns.copy()
        updating_columns.remove(pk)

        stmt = "INSERT INTO content.{} ".format(table)
        stmt += " ({}) ".format(','.join(columns))
        stmt += " VALUES ({}) ".format(','.join(['%s'] * len(columns)))
        stmt += " ON CONFLICT ({}) DO UPDATE SET ".format(pk)
        stmt += ",".join(
            [" {0}=EXCLUDED.{0}".format(column) for column in updating_columns]
        )
        stmt += ";"

        try:
            for data_chunk in more_itertools.ichunked(data,
                                                      settings.bunch_insert):
                data = [row.as_tuple for row in data_chunk]
                self.cursor.executemany(stmt, data)
                self.connection.commit()
        except psycopg2.errors.ForeignKeyViolation as e:
            self.connection.rollback()
            raise ForeignKeyError("Table <{}> need foreign key. \n"
                                  "Reason: {}".format(table, e))
        except Exception as e:
            logger.warning("Reason: can't insert "
                           "to table <{}>:\n\t{}".format(table, e))

    def get_pk_table(self, table: str) -> str:
        """Узнать PK таблицы."""
        stmt = """
            SELECT a.attname FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = 'content.{}'::regclass
            AND i.indisprimary;
        """.format(table)
        self.cursor.execute(stmt)
        pk = self.cursor.fetchone()
        if pk and len(pk) > 0:
            return pk[0]
