import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('genre')
        verbose_name_plural = _('genres')

    def __str__(self):
        return self.name


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('full_name'), max_length=255)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('person')
        verbose_name_plural = _('persons')
        indexes = [
            models.Index(
                fields=['full_name'],
                name='person_full_name_idx'
            ),
        ]

    def __str__(self):
        return self.full_name


class Filmwork(UUIDMixin, TimeStampedMixin):
    class Types(models.TextChoices):
        MOVIE = 'movie', _('movie')
        TV_SHOW = 'tv_show', _('tv_show')

    title = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)
    creation_date = models.DateField(_('creation_date'), null=True)
    rating = models.FloatField(_('rating'), blank=True, null=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    type = models.CharField(_('type'), max_length=16, choices=Types.choices,
                            default=Types.MOVIE,)
    genres = models.ManyToManyField(Genre, through='GenreFilmwork',
                                    verbose_name=_('genre'))
    persons = models.ManyToManyField(Person, through='PersonFilmwork',
                                     verbose_name=_('person'))
    certificate = models.CharField(_('certificate'), max_length=512,
                                   blank=True, null=True)
    file_path = models.FileField(_('file'), blank=True, null=True,
                                 upload_to='movies/')

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('filmwork')
        verbose_name_plural = _('filmworks')
        indexes = [
            models.Index(
                fields=['-creation_date'],
                name='film_work_creation_date_idx'
            ),
            models.Index(
                fields=['title'],
                name='film_work_title_idx'
            ),
        ]

    def __str__(self):
        return self.title


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE,
                                  verbose_name=_('filmwork'))
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE,
                              verbose_name=_('genre'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        verbose_name = _('genre_filmwork')
        verbose_name_plural = _('genre_filmworks')
        constraints = [
            models.UniqueConstraint(
                fields=['film_work_id', 'genre_id'],
                name='film_work_genre_idx',
            ),
        ]

    def __str__(self):
        return self.genre.name


class Roles(models.TextChoices):
    ACTOR = 'ACTOR', _('actor')
    DIRECTOR = 'DIRECTOR', _('director')
    WRITER = 'WRITER', _('writer')


class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE,
                                  verbose_name=_('filmwork'))
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               verbose_name=_('person'))
    role = models.CharField(max_length=16, choices=Roles.choices, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"
        verbose_name = _('person_filmwork')
        verbose_name_plural = _('person_filmworks')
        constraints = [
            models.UniqueConstraint(
                fields=['film_work_id', 'person_id', 'role'],
                name='film_work_person_role',
            ),
        ]

    def __str__(self):
        return self.role


class ElasticWatcher(models.Model):
    watcher = models.CharField(max_length=32, primary_key=True, null=False)
    modified_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "content\".\"elastic_watcher"
