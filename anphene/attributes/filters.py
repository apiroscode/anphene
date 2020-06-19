import django_filters
from django.db.models import Q
from graphene_django.filter import GlobalIDFilter, GlobalIDMultipleChoiceFilter

from core.graph.filters import EnumFilter
from core.graph.types import FilterInputObjectType
from core.graph.utils import from_global_id_strict_type
from core.utils.filters import filter_fields_containing_value
from .enums import AttributeTypeEnum
from .models import Attribute
from ..categories.models import Category
from ..products.models import Product


def filter_attribute_type(qs, _, value):
    if value == AttributeTypeEnum.VARIANT:
        qs = qs.filter(input_type="dropdown")
    return qs


def filter_attributes_by_product_types(qs, field, value):
    if not value:
        return qs

    if field == "in_category":
        category_id = from_global_id_strict_type(value, only_type="Category", field=field)
        category = Category.objects.filter(pk=category_id).first()

        if category is None:
            return qs.none()

        tree = category.get_descendants(include_self=True)
        product_qs = Product.objects.filter(category__in=tree)

    elif field == "in_collection":
        collection_id = from_global_id_strict_type(value, only_type="Collection", field=field)
        product_qs = Product.objects.filter(collections__id=collection_id)

    else:
        raise NotImplementedError(f"Filtering by {field} is unsupported")

    product_types = set(product_qs.values_list("product_type_id", flat=True))
    return qs.filter(
        Q(product_types__in=product_types) | Q(product_variant_types__in=product_types)
    )


class AttributeFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("slug", "name"))
    ids = GlobalIDMultipleChoiceFilter(field_name="id")
    input_type = EnumFilter(input_class=AttributeTypeEnum, method=filter_attribute_type)

    in_collection = GlobalIDFilter(method=filter_attributes_by_product_types)
    in_category = GlobalIDFilter(method=filter_attributes_by_product_types)

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
