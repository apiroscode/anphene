import graphene

from core.graph.types import SortInputObjectType


class SupplierSortField(graphene.Enum):
    NAME = "name"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {SupplierSortField.NAME.name: "name"}
        if self.name in descriptions:
            return f"Sort suppliers by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class SupplierSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = SupplierSortField
        type_name = "supplier"
