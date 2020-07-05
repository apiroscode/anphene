import graphene
import graphene_django_optimizer as gql_optimizer
from django.contrib.auth import models as auth_models
from graphene import relay

from core.exceptions import PermissionDenied
from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import FilterInputConnectionField
from core.graph.types import Permission
from core.graph.utils import from_global_id_strict_type
from core.utils import format_permissions_for_display
from . import models
from .filters import StaffUserInput
from ..core.permissions import UserPermissions
from ..regions.dataloader import SubDistrictByIdLoader


class Address(CountableDjangoObjectType):
    is_default_shipping_address = graphene.Boolean(
        required=False, description="Address is user's default shipping address."
    )

    class Meta:
        description = "Represents user address data."
        interfaces = [relay.Node]
        model = models.Address

    @staticmethod
    def resolve_is_default_shipping_address(root: models.Address, _info):
        """Look if the address is the default shipping address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_shipping_address_pk"):
            return None

        user_default_shipping_address_pk = getattr(root, "user_default_shipping_address_pk")
        if user_default_shipping_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def resolve_sub_districts(root: models.Address, info):
        return SubDistrictByIdLoader(info.context).load(root.sub_district_id)


class UserPermission(Permission):
    source_permission_groups = graphene.List(
        graphene.NonNull("anphene.users.types.Group"),
        description="List of user permission groups which contains this permission.",
        user_id=graphene.Argument(
            graphene.ID, description="ID of user whose groups should be returned.", required=True,
        ),
        required=False,
    )

    def resolve_source_permission_groups(root: Permission, _info, user_id, **_kwargs):
        user_id = from_global_id_strict_type(user_id, only_type="User", field="pk")
        groups = auth_models.Group.objects.filter(user__pk=user_id, permissions__name=root.name)
        return groups


class User(CountableDjangoObjectType):
    addresses = graphene.List(Address, description="List of all user's addresses.")

    user_permissions = graphene.List(UserPermission, description="List of user's permissions.")
    groups = graphene.List("anphene.users.types.Group", description="List of user's groups.",)

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node]
        model = models.User
        only_fields = [
            "id",
            "email",
            "note",
            "date_joined",
            "is_active",
            "is_staff",
            "last_login",
            "name",
            "id_card",
            "default_shipping_address",
            "balance",
        ]

    @staticmethod
    def resolve_addresses(root: models.User, _info, **_kwargs):
        return root.addresses.annotate_default(root).all()

    @staticmethod
    def resolve_user_permissions(root: models.User, _info, **_kwargs):
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="groups")
    def resolve_groups(root: models.User, _info, **_kwargs):
        return root.groups.all()

    @staticmethod
    def resolve_id_card(root: models.User, info, **_kwargs):
        if not root.id_card:
            return ""

        return info.context.build_absolute_uri(root.id_card.url)


class StaffNotificationRecipient(CountableDjangoObjectType):
    user = graphene.Field(
        User, description="Returns a user subscribed to email notifications.", required=False,
    )
    email = graphene.String(
        description=("Returns email address of a user subscribed to email notifications."),
        required=False,
    )
    active = graphene.Boolean(description="Determines if a notification active.")

    class Meta:
        description = (
            "Represents a recipient of email notifications send by Saleor, "
            "such as notifications about new orders. Notifications can be "
            "assigned to staff users or arbitrary email addresses."
        )
        interfaces = [relay.Node]
        model = models.StaffNotificationRecipient
        only_fields = ["user", "active"]

    @staticmethod
    def resolve_user(root: models.StaffNotificationRecipient, info):
        user = info.context.user
        if user == root.user or user.has_perm(UserPermissions.MANAGE_STAFF):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.StaffNotificationRecipient, _info):
        return root.get_email()


class Group(CountableDjangoObjectType):
    users = graphene.List(User, description="List of group users")
    permissions = graphene.List(Permission, description="List of group permissions")
    available_staff = FilterInputConnectionField(User, filter=StaffUserInput())

    class Meta:
        description = "Represents permission group data."
        interfaces = [relay.Node]
        model = auth_models.Group
        only_fields = ["name", "permissions", "id"]

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="user_set")
    def resolve_users(root: auth_models.Group, _info):
        return root.user_set.all()

    @staticmethod
    def resolve_permissions(root: auth_models.Group, _info):
        permissions = root.permissions.prefetch_related("content_type").order_by("codename")
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_available_staff(root: auth_models.Group, info, **kwargs):
        user = info.context.user
        qs = models.User.objects.staff().exclude(id=user.id).exclude(groups=root)
        return qs.distinct()
