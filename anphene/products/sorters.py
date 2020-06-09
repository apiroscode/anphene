# PRODUCT TYPE
# ============
import graphene

from core.graph.types import SortInputObjectType


class ProductTypeSortField(graphene.Enum):
    NAME = "name"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {ProductTypeSortField.NAME.name: "name"}
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductTypeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ProductTypeSortField
        type_name = "product types"
