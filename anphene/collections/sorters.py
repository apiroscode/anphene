import graphene
from django.db.models import Count

from core.graph.types import SortInputObjectType


class CollectionSortField(graphene.Enum):
    NAME = "name"
    AVAILABILITY = "is_published"
    PRODUCT_COUNT = "product_count"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            CollectionSortField.NAME,
            CollectionSortField.AVAILABILITY,
            CollectionSortField.PRODUCT_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort collections by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_product_count(queryset):
        return queryset.annotate(product_count=Count("collectionproduct__id"))


class CollectionSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = CollectionSortField
        type_name = "collections"
