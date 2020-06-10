import graphene

from core.graph.types import SortInputObjectType


class UserSortField(graphene.Enum):
    NAME = "name"
    EMAIL = "email"
    # ORDER_COUNT = ["order_count", "email"]

    @property
    def description(self):
        if self.name in UserSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort users by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class UserSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = UserSortField
        type_name = "users"


class GroupSortField(graphene.Enum):
    NAME = "name"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [GroupSortField.NAME]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort group accounts by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class GroupSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = GroupSortField
        type_name = "group"
