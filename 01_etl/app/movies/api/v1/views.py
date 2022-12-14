from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import Filmwork, Roles


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):
        def _aggregate_person(role):
            return ArrayAgg('persons__full_name', distinct=True,
                            filter=Q(personfilmwork__role=role))

        return Filmwork.objects.all().values(
            'id', 'title', 'description', 'creation_date', 'rating', 'type',
        ).annotate(
            genres=ArrayAgg('genres__name', distinct=True),
        ).annotate(
            actors=_aggregate_person(role=Roles.ACTOR),
            directors=_aggregate_person(role=Roles.DIRECTOR),
            writers=_aggregate_person(role=Roles.WRITER),
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset,
            self.paginate_by,
        )

        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev":
                page.previous_page_number() if page.has_previous() else None,
            "next":
                page.next_page_number() if page.has_next() else None,
            "results": list(queryset),
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        return self.object
