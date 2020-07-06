import graphene
from django.db import transaction

from core.exceptions import PermissionDenied
from core.graph.mutations import ModelDeleteMutation, ModelMutation
from .. import events as account_events
from ..emails import send_set_password_email_with_url
from ..types import Address, AddressInput, User
from ...core.permissions import UserPermissions
from ...utils.address import AddressValidation

SHIPPING_ADDRESS_FIELD = "default_shipping_address"
INVALID_TOKEN = "Invalid or expired token."


def can_edit_address(user, address):
    """Determine whether the user can edit the given address.

    This method assumes that an address can be edited by:
    - users with proper permissions (staff)
    - customers associated to the given address.
    """
    return (
        user.has_perm(UserPermissions.MANAGE_CUSTOMERS)
        or user.addresses.filter(pk=address.pk).exists()
    )


class BaseAddressUpdate(ModelMutation, AddressValidation):
    """Base mutation for address update used by staff and account."""

    user = graphene.Field(User, description="A user object for which the address was edited.")

    class Arguments:
        id = graphene.ID(description="ID of the address to update.", required=True)
        input = AddressInput(description="Fields required to update the address.", required=True)

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, info, instance, data):
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        if not can_edit_address(info.context.user, instance):
            raise PermissionDenied()
        return super().clean_input(info, instance, data)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info=info, instance=instance, data=data.get("input"))
        address = cls.validate_address(info, data, instance)
        user = address.user_addresses.first()
        cls.save(info, address, cleaned_input)
        cls._save_m2m(info, address, cleaned_input)
        success_response = cls.success_response(address)
        success_response.user = user
        success_response.address = address
        return success_response


class BaseAddressDelete(ModelDeleteMutation):
    """Base mutation for address delete used by staff and customers."""

    user = graphene.Field(User, description="A user instance for which the address was deleted.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the address to delete.")

    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        # Method check_permissions cannot be used for permission check, because
        # it doesn't have the address instance.
        if not can_edit_address(info.context.user, instance):
            raise PermissionDenied()
        return super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, Address)
        if instance:
            cls.clean_instance(info, instance)

        db_id = instance.id

        # Return the first user that the address is assigned to. There is M2M
        # relation between users and addresses, but in most cases address is
        # related to only one user.
        user = instance.user_addresses.first()

        instance.delete()
        instance.id = db_id

        # Refresh the user instance to clear the default addresses. If the
        # deleted address was used as default, it would stay cached in the
        # user instance and the invalid ID returned in the response might cause
        # an error.
        user.refresh_from_db()

        response = cls.success_response(instance)
        if not user.default_shipping_address and user.addresses.first():
            user.default_shipping_address = user.addresses.first()
        response.user = user
        return response


class UserInput(graphene.InputObjectType):
    name = graphene.String(description="Given name.")
    email = graphene.String(description="The unique email address of the user.")
    is_active = graphene.Boolean(required=False, description="User account is active.")
    note = graphene.String(description="A note about the user.")


class UserAddressInput(graphene.InputObjectType):
    default_shipping_address = AddressInput(description="Shipping address of the customer.")


class CustomerInput(UserInput, UserAddressInput):
    pass


class UserCreateInput(CustomerInput):
    redirect_url = graphene.String(
        description=(
            "URL of a view where users should be redirected to "
            "set the password. URL in RFC 1808 format."
        )
    )


class BaseCustomerCreate(ModelMutation, AddressValidation):
    """Base mutation for customer create used by staff and account."""

    class Arguments:
        input = UserCreateInput(description="Fields required to create a customer.", required=True)

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, info, instance, data):
        shipping_address_data = data.pop(SHIPPING_ADDRESS_FIELD, None)
        cleaned_input = super().clean_input(info, instance, data)

        if shipping_address_data:
            shipping_address = cls.validate_address(
                info, shipping_address_data, instance=getattr(instance, SHIPPING_ADDRESS_FIELD),
            )
            cleaned_input[SHIPPING_ADDRESS_FIELD] = shipping_address

        return cleaned_input

    @classmethod
    @transaction.atomic
    def save(cls, info, instance, cleaned_input):
        # FIXME: save address in user.addresses as well
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address

        is_creation = instance.pk is None
        super().save(info, instance, cleaned_input)

        if default_shipping_address:
            instance.addresses.add(default_shipping_address)

        # The instance is a new object in db, create an event
        if is_creation:
            account_events.customer_account_created_event(user=instance)

        if cleaned_input.get("redirect_url"):
            send_set_password_email_with_url(cleaned_input.get("redirect_url"), instance)
