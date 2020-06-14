import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.graph.filters import EnumFilter
from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .enums import CollectionPublished
from .models import Collection


def filter_collection_publish(qs, _, value):
    if value == CollectionPublished.PUBLISHED:
        qs = qs.filter(is_published=True)
    elif value == CollectionPublished.HIDDEN:
        qs = qs.filter(is_published=False)
    return qs


class CollectionFilter(django_filters.FilterSet):
    published = EnumFilter(input_class=CollectionPublished, method=filter_collection_publish)
    search = django_filters.CharFilter(method=filter_fields_containing_value("slug", "name"))
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Collection
        fields = ["published", "search"]


class CollectionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CollectionFilter
