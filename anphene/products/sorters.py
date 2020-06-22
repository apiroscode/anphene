import graphene
from django.db.models import Min

from core.graph.types import SortInputObjectType


# PRODUCT TYPE
# ============
class ProductTypeSortField(graphene.Enum):
    NAME = "name"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {ProductTypeSortField.NAME.name: "name"}
        if self.name in descriptions:
            return f"Sort products type by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductTypeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductTypeSortField
        type_name = "product types"


# PRODUCT
# =======
class ProductSortField(graphene.Enum):
    NAME = "name"
    SLUG = "slug"
    PRICE = "price"
    UPDATED_AT = "updated_at"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ProductSortField.NAME.name: "name",
            ProductSortField.SLUG.name: "slug",
            ProductSortField.PRICE.name: "Minimal price from product variants",
            ProductSortField.UPDATED_AT.name: "update date",
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_price(queryset):
        return queryset.annotate(price=Min("variants__price"))


class ProductSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductSortField
        type_name = "product"
