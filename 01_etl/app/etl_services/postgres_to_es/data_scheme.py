from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Person(TypedDict):
    id: UUID
    name: str


class MovieEsModel(BaseModel):
    id: UUID
    title: str
    imdb_rating: float = Field(None, alias='rating')
    genre: Optional[list[str]]
    description: Optional[str]
    directors: Optional[list[Person]]
    actors: Optional[list[Person]]
    writers: Optional[list[Person]]
    director: Optional[list[str]]
    actors_names: Optional[list[str]]
    writers_names: Optional[list[str]]
