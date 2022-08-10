import pytest

from sqlite_to_postgres.data_classes import DATACLASSES_MAP


@pytest.mark.parametrize(
    'table',
    # хардкод списка по условию задания
    ['genre', 'genre_film_work', 'person_film_work', 'person', 'film_work'],
)
def test_count_rows(conn_db: tuple, table: str):
    """Кол-во записей совпадает в SQLite-доноре и в Postgres-реципиенте."""
    sqlite_cursor, pg_cursor = conn_db

    sqlite_stmt = "SELECT COUNT(*) FROM {} ;".format(table)
    sqlite_cursor.execute(sqlite_stmt)
    donor_count = sqlite_cursor.fetchone()[0]

    pg_stmt = "SELECT COUNT(*) FROM content.{} ;".format(table)
    pg_cursor.execute(pg_stmt)
    recipient_count = pg_cursor.fetchone()[0]

    assert donor_count == recipient_count


@pytest.mark.parametrize(
    'table',
    ['genre', 'genre_film_work', 'person_film_work', 'person', 'film_work'],
)
def test_tables_content(conn_db: tuple, table: str):
    """Все записи совпадают в SQLite-доноре и в Postgres-реципиенте."""
    sqlite_cursor, pg_cursor = conn_db
    stmt = """
        SELECT a.attname FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid
            AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = 'content.{}'::regclass
        AND i.indisprimary;
    """.format(table)
    pg_cursor.execute(stmt)
    pk = pg_cursor.fetchone()[0]

    pg_stmt = "SELECT * FROM content.{} ".format(table)
    pg_cursor.execute(pg_stmt)
    recipient_data = pg_cursor.fetchall()
    for row in recipient_data:
        sqlite_stmt = "SELECT * FROM {} WHERE {} = ? ;".format(table, pk)
        sqlite_cursor.execute(sqlite_stmt, (row[pk],))
        donor = sqlite_cursor.fetchone()
        dt_class = DATACLASSES_MAP.get(table)
        sqlite_obj = dt_class(**donor)
        pg_obj = dt_class(**row)

        assert sqlite_obj == pg_obj
