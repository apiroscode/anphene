import django_filters

from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .models import Page


class PageFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("content", "slug", "title")
    )

    class Meta:
        model = Page
        fields = ["search"]


class PageFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PageFilter
