from django_filters import rest_framework as filters

from funkwhale_api.common import fields
from funkwhale_api.common import filters as common_filters
from funkwhale_api.common import search as search_config
from funkwhale_api.moderation import filters as moderation_filters
import operator

from django_filters import rest_framework as filters
import django_filters
from functools import reduce

from django.conf import settings
from django.db import connection
from django.db.models import DecimalField
from django.db.models.expressions import Value

from . import models
from . import utils

def filter_tags(queryset, name, value):
    non_empty_tags = [v.lower() for v in value if v]
    for tag in non_empty_tags:
        queryset = queryset.filter(tagged_items__tag__name=tag).distinct()
    return queryset

TAG_FILTER = common_filters.MultipleQueryFilter(method=filter_tags)
DEFAULT_SEARCH_RESULT_SIZE = 250

class SearchFilter(filters.Filter):
    def _tokenize_query(self, query):
        """Split query string into individual terms"""
        return query.split(' ')

    def _add_prefix_wildcards(self, terms):
        """Add PostgreSQL prefix wildcards to search terms"""
        return [f"{term}:*" for term in terms if term]

    def _build_ts_query(self, search_term):
        """Build the full text search query with prefix matching"""
        terms = self._tokenize_query(search_term)
        wildcard_terms = self._add_prefix_wildcards(terms)
        return " | ".join(wildcard_terms)

    def _execute_search_query(self, qs, query_terms):
        """Execute the PostgreSQL full text search query"""
        document_vector = "ts_document_vector"
        
        sql = """
            WITH tsq AS (
                SELECT to_tsquery('english', %s) AS query)
            SELECT id, rank
            FROM (
                SELECT id, ts_rank_cd({document_vector},
                                    query, 2|8) AS rank
                FROM {table}, tsq
                WHERE ts_document_vector @@ query = true
                ) matches
            ORDER BY rank DESC LIMIT 10;
        """.format(table=self.table, document_vector=document_vector)

        return self._get_search_results(qs, sql, [query_terms])

    def _get_search_results(self, qs, sql, sql_params):
        """Process raw SQL results into a queryset with rank annotations"""
        results = qs.model.objects.raw(sql, sql_params)
        return_objs = []

        for obj in results:
            return_objs.append(
                qs.filter(id=obj.id).annotate(
                    rank=Value(obj.rank, DecimalField())
                )
            )

        if return_objs:
            return reduce(operator.or_, return_objs)
        return qs.model.objects.none()

    def filter(self, qs, search_term, threshold=0.4):
        """Main filter method that handles the search"""
        if not search_term:
            return qs

        # Get configured result size
        self.search_result_size = getattr(
            qs.model, '_search_result_size', 
            getattr(settings, 'MAX_SEARCH_RESULT_SIZE', DEFAULT_SEARCH_RESULT_SIZE)
        )

        # Build table name for the query
        self.table = f"{qs.model._meta.app_label}_{qs.model.__name__.lower()}"

        # Build and execute search
        query_terms = self._build_ts_query(search_term)
        results = self._execute_search_query(qs, query_terms)

        return results if results.exists() else qs.none()

class ArtistFilter(moderation_filters.HiddenContentFilterSet):
    q = fields.SearchFilter(search_fields=["name"])
    playable = filters.BooleanFilter(field_name="_", method="filter_playable")

    class Meta:
        model = models.Artist
        fields = {
            "name": ["exact", "iexact", "startswith", "icontains"],
            "playable": "exact",
        }
        hidden_content_fields_mapping = moderation_filters.USER_FILTER_CONFIG["ARTIST"]

    def filter_playable(self, queryset, name, value):
        actor = utils.get_actor_from_request(self.request)
        return queryset.playable_by(actor, value)


class TrackFilter(moderation_filters.HiddenContentFilterSet):
    q = fields.SearchFilter(search_fields=["title", "album__title", "artist__name"])
    playable = filters.BooleanFilter(field_name="_", method="filter_playable")
    id = common_filters.MultipleQueryFilter(coerce=int)

    class Meta:
        model = models.Track
        fields = {
            "title": ["exact", "iexact", "startswith", "icontains"],
            "playable": ["exact"],
            "id": ["exact"],
            "artist": ["exact"],
            "album": ["exact"],
            "license": ["exact"],
        }
        hidden_content_fields_mapping = moderation_filters.USER_FILTER_CONFIG["TRACK"]

    def filter_playable(self, queryset, name, value):
        actor = utils.get_actor_from_request(self.request)
        return queryset.playable_by(actor, value)


class UploadFilter(filters.FilterSet):
    library = filters.CharFilter("library__uuid")
    track = filters.UUIDFilter("track__uuid")
    track_artist = filters.UUIDFilter("track__artist__uuid")
    album_artist = filters.UUIDFilter("track__album__artist__uuid")
    library = filters.UUIDFilter("library__uuid")
    playable = filters.BooleanFilter(field_name="_", method="filter_playable")
    search = SearchFilter()
    q = fields.SmartSearchFilter(
        config=search_config.SearchConfig(
            search_fields={
                "recording_name": {"to": "recording_name"},
                "recording_date": {"to": "recording_date"},
                "recording_special_sounds": {"to": "recording_special_sounds"},
                "recording_start_location": {"to": "recording_start_location"},
                "recording_thoughts": {"to": "recording_thoughts"},
                "recording_description": {"to": "recording_description"},
                "recording_route": {"to": "recording_route"},
                "title": {"to": "track__title"},
            },
            filter_fields={
                "artist": {"to": "track__artist__name__iexact"},
                "mimetype": {"to": "mimetype"},
                "album": {"to": "track__album__title__iexact"},
                "title": {"to": "track__title__iexact"},
                "status": {"to": "import_status"},
            },
        )
    )

    class Meta:
        model = models.Upload
        fields = [
            "playable",
            "import_status",
            "mimetype",
            "track",
            "track_artist",
            "album_artist",
            "library",
            "import_reference",
        ]

    def filter_playable(self, queryset, name, value):
        actor = utils.get_actor_from_request(self.request)
        return queryset.playable_by(actor, value)


class AlbumFilter(moderation_filters.HiddenContentFilterSet):
    playable = filters.BooleanFilter(field_name="_", method="filter_playable")
    q = fields.SearchFilter(search_fields=["title", "artist__name"])

    class Meta:
        model = models.Album
        fields = ["playable", "q", "artist"]
        hidden_content_fields_mapping = moderation_filters.USER_FILTER_CONFIG["ALBUM"]

    def filter_playable(self, queryset, name, value):
        actor = utils.get_actor_from_request(self.request)
        return queryset.playable_by(actor, value)
