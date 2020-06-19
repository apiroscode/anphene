import graphene

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
    MINIMAL_VARIANT_PRICE = "minimal_variant_price"
    UPDATED_AT = "updated_at"
    PRODUCT_TYPE_NAME = "product_type__name"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ProductSortField.NAME.name: "name",
            ProductSortField.SLUG.name: "slug",
            ProductSortField.MINIMAL_VARIANT_PRICE.name: "a minimal price of a product's variant",
            ProductSortField.UPDATED_AT.name: "update date",
            ProductSortField.PRODUCT_TYPE_NAME.name: "type",
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductSortField
        type_name = "product"
