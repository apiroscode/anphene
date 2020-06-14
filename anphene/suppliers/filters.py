import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .models import Supplier


class SupplierFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("name", "email", "phone")
    )
    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = Supplier
        fields = ["search"]


class SupplierFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SupplierFilter
