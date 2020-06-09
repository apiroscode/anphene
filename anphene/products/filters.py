import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.graph.filters import EnumFilter
from core.graph.types import FilterInputObjectType
from core.utils.filters import filter_fields_containing_value
from .enums import ProductTypeConfigurable
from .models import ProductType


# PRODUCT TYPE
# ============
def filter_product_type_configurable(qs, _, value):
    if value == ProductTypeConfigurable.CONFIGURABLE:
        qs = qs.filter(has_variants=True)
    elif value == ProductTypeConfigurable.SIMPLE:
        qs = qs.filter(has_variants=False)
    return qs


class ProductTypeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name", "slug"))

    configurable = EnumFilter(
        input_class=ProductTypeConfigurable, method=filter_product_type_configurable
    )

    ids = GlobalIDMultipleChoiceFilter(field_name="id")

    class Meta:
        model = ProductType
        fields = ["search", "configurable"]


class ProductTypeFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductTypeFilter
