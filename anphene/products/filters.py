import functools
import operator
from collections import defaultdict

import django_filters
from django.db.models import Q, Subquery
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.graph.filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter
from core.graph.types import FilterInputObjectType
from core.graph.types.common import PriceRangeInput
from core.graph.utils import get_nodes
from core.utils.filters import filter_fields_containing_value
from .enums import ProductTypeConfigurable, StockAvailability
from .models import Product, ProductType, ProductVariant
from ..attributes.models import Attribute
from ..attributes.types import AttributeInput
from ..categories import types as categories_types
from ..collections import types as collections_types
from ..search.backends import picker


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


# PRODUCT
# =======
def filter_search(qs, _, value):
    if value:
        search = picker.pick_backend()
        qs &= search(value).distinct()
    return qs


def filter_products_by_categories(qs, categories):
    categories = [category.get_descendants(include_self=True) for category in categories]
    ids = {category.id for tree in categories for category in tree}
    return qs.filter(category__in=ids)


def filter_categories(qs, _, value):
    if value:
        categories = get_nodes(value, categories_types.Category)
        qs = filter_products_by_categories(qs, categories)
    return qs


def filter_has_category(qs, _, value):
    return qs.filter(category__isnull=not value)


def filter_products_by_collections(qs, collections):
    return qs.filter(collections__in=collections)


def filter_collections(qs, _, value):
    if value:
        collections = get_nodes(value, collections_types.Collection)
        qs = filter_products_by_collections(qs, collections)
    return qs


def filter_products_by_minimal_price(qs, minimal_price_lte=None, minimal_price_gte=None):
    if minimal_price_lte:
        qs = qs.filter(minimal_variant_price_amount__lte=minimal_price_lte)
    if minimal_price_gte:
        qs = qs.filter(minimal_variant_price_amount__gte=minimal_price_gte)
    return qs


def filter_minimal_price(qs, _, value):
    qs = filter_products_by_minimal_price(
        qs, minimal_price_lte=value.get("lte"), minimal_price_gte=value.get("gte")
    )
    return qs


def _clean_product_attributes_filter_input(filter_value):
    attributes = Attribute.objects.prefetch_related("values")
    attributes_map = {attribute.slug: attribute.pk for attribute in attributes}
    values_map = {
        attr.slug: {value.slug: value.pk for value in attr.values.all()} for attr in attributes
    }
    queries = defaultdict(list)
    # Convert attribute:value pairs into a dictionary where
    # attributes are keys and values are grouped in lists
    for attr_name, val_slugs in filter_value:
        if attr_name not in attributes_map:
            raise ValueError("Unknown attribute name: %r" % (attr_name,))
        attr_pk = attributes_map[attr_name]
        attr_val_pk = [
            values_map[attr_name][val_slug]
            for val_slug in val_slugs
            if val_slug in values_map[attr_name]
        ]
        queries[attr_pk] += attr_val_pk

    return queries


def filter_products_by_attributes_values(qs, queries):
    # Combine filters of the same attribute with OR operator
    # and then combine full query with AND operator.
    combine_and = [
        Q(**{"attributes__values__pk__in": values_pk})
        | Q(**{"variants__attributes__values__pk__in": values_pk})
        for _, values_pk in queries.items()
    ]
    query = functools.reduce(operator.and_, combine_and)
    qs = qs.filter(query).distinct()
    return qs


def filter_products_by_attributes(qs, filter_value):
    queries = _clean_product_attributes_filter_input(filter_value)
    return filter_products_by_attributes_values(qs, queries)


def filter_attributes(qs, _, value):
    if value:
        value_list = []
        for v in value:
            slug = v["slug"]
            values = v.get("values", [])
            value_list.append((slug, values))
        qs = filter_products_by_attributes(qs, value_list)
    return qs


def filter_products_by_stock_availability(qs, stock_availability):
    total_stock = (
        ProductVariant.objects.annotate_available_quantity()
        .filter(available_quantity__lte=0)
        .values_list("product_id", flat=True)
    )
    if stock_availability == StockAvailability.IN_STOCK:
        qs = qs.exclude(id__in=Subquery(total_stock))
    elif stock_availability == StockAvailability.OUT_OF_STOCK:
        qs = qs.filter(id__in=Subquery(total_stock))
    return qs


def filter_stock_availability(qs, _, value):
    if value:
        qs = filter_products_by_stock_availability(qs, value)
    return qs


class ProductFilter(django_filters.FilterSet):
    is_published = django_filters.BooleanFilter()
    collections = GlobalIDMultipleChoiceFilter(method=filter_collections)
    categories = GlobalIDMultipleChoiceFilter(method=filter_categories)
    has_category = django_filters.BooleanFilter(method=filter_has_category)
    minimal_price = ObjectTypeFilter(
        input_class=PriceRangeInput,
        method=filter_minimal_price,
        field_name="minimal_price_amount",
    )
    attributes = ListObjectTypeFilter(input_class=AttributeInput, method=filter_attributes)
    stock_availability = EnumFilter(
        input_class=StockAvailability, method=filter_stock_availability
    )
    product_types = GlobalIDMultipleChoiceFilter(field_name="product_type")
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = Product
        fields = [
            "is_published",
            "collections",
            "categories",
            "has_category",
            "minimal_price",
            "attributes",
            "stock_availability",
            "product_type",
            "search",
        ]


class ProductFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = ProductFilter
