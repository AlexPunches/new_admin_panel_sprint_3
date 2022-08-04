from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from movies.models import (Filmwork, Genre, GenreFilmwork, Person,
                           PersonFilmwork)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ('genre',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ('full_name', 'id')


class PersonFilmworkInline(admin.StackedInline):
    model = PersonFilmwork
    raw_id_fields = ("person",)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline,)

    list_display = ('title', 'type', 'get_genres', 'creation_date', 'rating',
                    'get_actors', 'get_directors', 'get_writers')
    list_filter = ('type',)
    search_fields = ('title', 'description', 'id')
    list_prefetch_related = ('persons', 'genres',)

    def get_queryset(self, request):
        queryset = (
                super()
                .get_queryset(request)
                .prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genres.all()])

    def get_actors(self, obj):
        return ', '.join(
            [person.full_name for person
                in obj.persons.filter(personfilmwork__role='actor')]
        )

    def get_directors(self, obj):
        return ', '.join(
            [person.full_name for person
                in obj.persons.filter(personfilmwork__role='director')]
        )

    def get_writers(self, obj):
        return ', '.join(
            [person.full_name for person
                in obj.persons.filter(personfilmwork__role='writer')]
        )

    get_genres.short_description = _('genres')
    get_actors.short_description = _('actors')
    get_directors.short_description = _('directors')
    get_writers.short_description = _('writers')
