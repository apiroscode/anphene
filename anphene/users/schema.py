import graphene

from core.decorators import one_of_permissions_required, permission_required
from core.graph.fields import FilterInputConnectionField
from core.graph.types import Permission
from .filters import CustomerFilterInput, GroupFilterInput, StaffUserInput
from .mutations.auth import Login, Logout, PasswordChange, RequestPasswordReset, SetPassword
from .mutations.customers import (
    AddressCreate,
    AddressDelete,
    AddressSetDefault,
    AddressUpdate,
    CustomerCreate,
    CustomerDelete,
    CustomerUpdate,
)
from .mutations.groups import (
    GroupBulkDelete,
    GroupCreate,
    GroupDelete,
    GroupStaffAssign,
    GroupStaffUnassign,
    GroupUpdate,
)
from .mutations.staff import (
    StaffCreate,
    StaffDelete,
    StaffUpdate,
)
from .mutations_bulk.customers import CustomerBulkDelete
from .mutations_bulk.staff import StaffBulkActivate, StaffBulkDelete
from .resolvers import (
    resolve_address,
    resolve_all_permissions,
    resolve_customers,
    resolve_groups,
    resolve_staff_users,
    resolve_user,
)
from .sorters import GroupSortingInput, UserSortingInput
from .types import Address, Group, User
from ..core.permissions import GroupPermissions, UserPermissions


class UserQueries(graphene.ObjectType):
    address = graphene.Field(
        Address,
        id=graphene.Argument(graphene.ID, description="ID of an address.", required=True),
        description="Look up an address by ID.",
    )
    customers = FilterInputConnectionField(
        User,
        filter=CustomerFilterInput(description="Filtering options for customers."),
        sort_by=UserSortingInput(description="Sort customers."),
        description="List of the shop's customers.",
    )
    all_permissions = graphene.List(Permission, description="List of store permissions.")
    groups = FilterInputConnectionField(
        Group,
        filter=GroupFilterInput(description="Filtering options for permission groups."),
        sort_by=GroupSortingInput(description="Sort permission groups."),
        description="List of permission groups.",
    )
    group = graphene.Field(
        Group,
        id=graphene.Argument(graphene.ID, description="ID of the group.", required=True),
        description="Look up permission group by ID.",
    )
    me = graphene.Field(User, description="Return the currently authenticated user.")
    staff_users = FilterInputConnectionField(
        User,
        filter=StaffUserInput(description="Filtering options for staff users."),
        sort_by=UserSortingInput(description="Sort staff users."),
        description="List of the shop's staff users.",
    )
    user = graphene.Field(
        User,
        id=graphene.Argument(graphene.ID, description="ID of the user.", required=True),
        description="Look up a user by ID.",
    )

    def resolve_address(self, info, id):
        return resolve_address(info, id)

    @permission_required(UserPermissions.MANAGE_CUSTOMERS)
    def resolve_customers(self, info, **kwargs):
        return resolve_customers(info, **kwargs)

    @permission_required(GroupPermissions.MANAGE_GROUPS)
    def resolve_all_permissions(self, info, **kwargs):
        return resolve_all_permissions(info, **kwargs)

    @permission_required(GroupPermissions.MANAGE_GROUPS)
    def resolve_groups(self, info, **kwargs):
        return resolve_groups(info, **kwargs)

    @permission_required(GroupPermissions.MANAGE_GROUPS)
    def resolve_group(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Group)

    def resolve_me(self, info):
        user = info.context.user
        return user if user.is_authenticated else None

    @permission_required(UserPermissions.MANAGE_STAFF)
    def resolve_staff_users(self, info, **kwargs):
        return resolve_staff_users(info, **kwargs)

    @one_of_permissions_required([UserPermissions.MANAGE_STAFF, UserPermissions.MANAGE_CUSTOMERS])
    def resolve_user(self, info, id):
        return resolve_user(info, id)


class UserMutations(graphene.ObjectType):
    # Auth Mutations
    login = Login.Field()
    logout = Logout.Field()
    set_password = SetPassword.Field()
    request_password_reset = RequestPasswordReset.Field()
    password_change = PasswordChange.Field()

    # Group Mutations
    group_create = GroupCreate.Field()
    group_update = GroupUpdate.Field()
    group_delete = GroupDelete.Field()
    group_bulk_delete = GroupBulkDelete.Field()
    group_staff_assign = GroupStaffAssign.Field()
    group_staff_unassign = GroupStaffUnassign.Field()

    # Staff Mutations
    staff_create = StaffCreate.Field()
    staff_update = StaffUpdate.Field()
    staff_delete = StaffDelete.Field()
    staff_bulk_activate = StaffBulkActivate.Field()
    staff_bulk_delete = StaffBulkDelete.Field()

    # Customers Mutations
    customer_create = CustomerCreate.Field()
    customer_update = CustomerUpdate.Field()
    customer_delete = CustomerDelete.Field()
    customer_bulk_delete = CustomerBulkDelete.Field()
    address_create = AddressCreate.Field()
    address_update = AddressUpdate.Field()
    address_delete = AddressDelete.Field()
    address_set_default = AddressSetDefault.Field()
