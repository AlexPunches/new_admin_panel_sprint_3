from datetime import datetime

from postgres_to_es import DbConnect


class WatcherError(Exception):
    pass


class Watcher(DbConnect):
    """Класс сохранения и получения состояния индексации Elastic's."""
    FILM_WORK = 'film_work'
    GENRE = 'genre'
    PERSON = 'person'
    TYPE = [
        (FILM_WORK, 'film_work'),
        (GENRE, 'genre'),
        (PERSON, 'person'),
    ]

    def __init__(self, *args, **kwargs):
        super(Watcher, self).__init__(*args, **kwargs)
        self.stack = set()
        self.were_lasts = self.get_all_was_finish()
        self.will_last = self.get_all_will_finish()

    def get_all_was_finish(self) -> dict[TYPE, datetime]:
        """Определяем на каком значении updates_at остановились прошлый раз."""
        _all = {}
        for watch_type in self.TYPE:
            _all[watch_type[0]] = self.get_last_finish(watch_type[0])
        return _all

    def get_all_will_finish(self) -> dict[TYPE, datetime]:
        """Определяем крайние updated_at после текущего импорта."""
        _all = {}
        for watch_type in self.TYPE:
            _all[watch_type[0]] = self.get_will_finish(watch_type[0])
        return _all

    def get_last_finish(self, watcher: TYPE) -> datetime:
        stmt = "SELECT modified_at FROM content.elastic_watcher "
        stmt += " WHERE watcher = %s ;"
        self.cursor.execute(stmt, [watcher])
        last_modified = self.cursor.fetchone()
        if last_modified and len(last_modified) > 0:
            return last_modified[0]

    def get_will_finish(self, watcher: TYPE) -> datetime:
        stmt = "SELECT max(updated_at) FROM content.{} ".format(watcher)
        self.cursor.execute(stmt)
        last_modified = self.cursor.fetchone()
        if last_modified and len(last_modified) > 0:
            return last_modified[0]

    def finish(self) -> None:
        """Удачно завершаем импорт,
        устанавливая новые modified_at в elastic_watcher.
        """
        for _type, modified_at in self.will_last.items():
            self.set_last_finish(_type, modified_at)

    def set_last_finish(self, watcher: TYPE, modified_at: datetime) -> None:
        stmt = """
        INSERT INTO content.elastic_watcher (watcher, modified_at)
            VALUES (%s, %s)
        ON CONFLICT (watcher) DO UPDATE SET
            modified_at=EXCLUDED.modified_at;
        """
        self.cursor.execute(stmt, (watcher, modified_at))
        self.connection.commit()
