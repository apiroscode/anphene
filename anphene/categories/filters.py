import django_filters
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .models import Category
from ..core.filters import (
    filter_not_in_sales,
    filter_not_in_vouchers,
    filter_sales,
    filter_vouchers,
)


class CategoryFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("slug", "name"))
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    parent = GlobalIDFilter()

    # used in sales
    sales = GlobalIDMultipleChoiceFilter(method=filter_sales)
    not_in_sales = GlobalIDMultipleChoiceFilter(method=filter_not_in_sales)

    # used in vouchers
    vouchers = GlobalIDMultipleChoiceFilter(method=filter_vouchers)
    not_in_vouchers = GlobalIDMultipleChoiceFilter(method=filter_not_in_vouchers)

    class Meta:
        model = Category
        fields = ["search", "parent"]


class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CategoryFilter
