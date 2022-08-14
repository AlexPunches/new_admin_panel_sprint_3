from datetime import datetime
from enum import Enum

from postgres_to_es import DbConnect


class Tracked(str, Enum):
    """Список изменяемых сущностей,
    после изменения которых нужно обновить индекс ElasticSearch.
    """
    FILM_WORK = 'film_work'
    GENRE = 'genre'
    PERSON = 'person'


class ElasticIndexStateError(Exception):
    ...


class ElasticIndexState(DbConnect):
    """Класс сохранения и получения состояния индексации Elastic's."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.were_lasts = self.get_all_was_finish()
        self.will_last = self.get_all_will_finish()

    def get_all_was_finish(self) -> dict[Tracked, datetime]:
        """Определяем на каком значении updates_at остановились прошлый раз."""
        return {
            entity: self._get_last_finish(entity)
            for entity in Tracked
        }

    def get_all_will_finish(self) -> dict[Tracked, datetime]:
        """Определяем крайние updated_at после текущего импорта."""
        return {
            entity: self._get_will_finish(entity)
            for entity in Tracked
        }

    def finish(self) -> None:
        """Удачно завершаем импорт,
        устанавливая новые modified_at в elastic_watcher.
        """
        for _type, modified_at in self.will_last.items():
            self._set_last_finish(_type, modified_at)

    def _get_last_finish(self, entity: Tracked) -> datetime:
        stmt = "SELECT modified_at FROM content.elastic_watcher "
        stmt += " WHERE watcher = %s ;"
        self.cursor.execute(stmt, [entity])
        last_modified = self.cursor.fetchone()
        if last_modified and len(last_modified) > 0:
            return last_modified[0]
        return datetime.fromtimestamp(0)

    def _get_will_finish(self, entity: Tracked) -> datetime:
        stmt = "SELECT max(updated_at) FROM content.{} ".format(entity)
        self.cursor.execute(stmt)
        last_modified = self.cursor.fetchone()
        if last_modified and len(last_modified) > 0:
            return last_modified[0]

    def _set_last_finish(self, entity: Tracked, modified_at: datetime) -> None:
        stmt = """
        INSERT INTO content.elastic_watcher (watcher, modified_at)
            VALUES (%s, %s)
        ON CONFLICT (watcher) DO UPDATE SET
            modified_at=EXCLUDED.modified_at;
        """
        self.cursor.execute(stmt, (entity, modified_at))
        self.connection.commit()
