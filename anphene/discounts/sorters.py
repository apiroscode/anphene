import graphene

from core.graph.types import SortInputObjectType


class SaleSortField(graphene.Enum):
    NAME = "name"
    START_DATE = "start_date"
    END_DATE = "end_date"
    VALUE = "value"

    @property
    def description(self):
        if self.name in SaleSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort sales by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class SaleSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = SaleSortField
        type_name = "sales"


class VoucherSortField(graphene.Enum):
    CODE = "code"
    START_DATE = "start_date"
    END_DATE = "end_date"
    VALUE = "discount_value"
    USAGE_LIMIT = "usage_limit"
    MINIMUM_SPENT_AMOUNT = "min_spent_amount"

    @property
    def description(self):
        if self.name in VoucherSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort vouchers by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class VoucherSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = VoucherSortField
        type_name = "vouchers"
