import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.graph.filters import EnumFilter
from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .enums import AttributeTypeEnum
from .models import Attribute


def filter_attribute_type(qs, _, value):
    if value == AttributeTypeEnum.VARIANT:
        qs = qs.filter(input_type="dropdown")
    return qs


class AttributeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("slug", "name"))
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    input_type = EnumFilter(input_class=AttributeTypeEnum, method=filter_attribute_type)

    class Meta:
        model = Attribute
        fields = [
            "value_required",
            "visible_in_storefront",
            "filterable_in_storefront",
            "filterable_in_dashboard",
            "available_in_grid",
        ]


class AttributeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = AttributeFilter
