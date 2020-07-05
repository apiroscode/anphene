import django_filters

from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .models import Menu, MenuItem


class MenuFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))

    class Meta:
        model = Menu
        fields = ["search"]


class MenuItemFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))

    class Meta:
        model = MenuItem
        fields = ["search"]


class MenuFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MenuFilter


class MenuItemFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MenuItemFilter
