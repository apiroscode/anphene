import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter, GlobalIDFilter

from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .models import Category


class CategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("slug", "name"))
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    parent = GlobalIDFilter()

    class Meta:
        model = Category
        fields = ["search", "parent"]


class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CategoryFilter
