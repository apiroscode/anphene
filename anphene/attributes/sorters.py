import graphene
from django.db.models import QuerySet

from core.graph.enums import OrderDirection
from core.graph.types import SortInputObjectType


class AttributeSortField(graphene.Enum):
    NAME = "name"
    SLUG = "slug"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            AttributeSortField.NAME.name: "Sort attributes by name",
            AttributeSortField.SLUG.name: "Sort attributes by slug",
        }
        if self.name in descriptions:
            return descriptions[self.name]
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_dashboard_variant_position(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        # pylint: disable=no-member
        is_asc = sort_by["direction"] == OrderDirection.ASC.value  # type: ignore
        return queryset.variant_attributes_sorted(is_asc)

    @staticmethod
    def sort_by_dashboard_product_position(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        # pylint: disable=no-member
        is_asc = sort_by["direction"] == OrderDirection.ASC.value  # type: ignore
        return queryset.product_attributes_sorted(is_asc)


class AttributeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AttributeSortField
        type_name = "attributes"
