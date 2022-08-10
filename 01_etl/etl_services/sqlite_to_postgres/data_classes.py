import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime

import dateutil.parser as parser


@dataclass(slots=True)
class BaseDt:
    @classmethod
    def get_fields(cls) -> list[str]:
        return [column.name for column in fields(cls)]

    @property
    def as_tuple(self) -> tuple[str | None]:
        return tuple([self.__getattribute__(col) for col in self.get_fields()])


@dataclass()
class DatetimeStampedCreate:
    created_at: datetime

    def __post_init__(self):
        if type(self.created_at) == str:
            date = parser.parse(self.created_at)
            self.created_at = datetime.fromisoformat(date.isoformat())


@dataclass()
class DatetimeStamped(DatetimeStampedCreate):
    updated_at: datetime

    def __post_init__(self):
        super().__post_init__()
        if type(self.updated_at) == str:
            date = parser.parse(self.updated_at)
            self.updated_at = datetime.fromisoformat(date.isoformat())


@dataclass(slots=True)
class Genre(BaseDt, DatetimeStamped):
    name: str
    description: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(slots=True)
class GenreFilmWork(BaseDt, DatetimeStampedCreate):
    film_work_id: str
    genre_id: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(slots=True)
class PersonFilmWork(BaseDt, DatetimeStampedCreate):
    film_work_id: str
    person_id: str
    role: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(slots=True)
class Person(BaseDt, DatetimeStamped):
    full_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass(slots=True)
class FilmWork(BaseDt, DatetimeStamped):
    title: str
    creation_date: str
    description: str
    file_path: str
    type: str
    certificate: str | None = field(default=None)
    rating: float = field(default=0.0)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


DATACLASSES_MAP = {
    'genre': Genre,
    'genre_film_work': GenreFilmWork,
    'person_film_work': PersonFilmWork,
    'person': Person,
    'film_work': FilmWork,
}
