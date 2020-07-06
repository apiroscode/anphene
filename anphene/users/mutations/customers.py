from copy import copy

import graphene
from django.core.exceptions import ValidationError

from core.graph.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from .base import BaseAddressDelete, BaseAddressUpdate, BaseCustomerCreate, CustomerInput
from .. import events as account_events, models
from ..types import Address, AddressInput, User
from ..utils import CustomerDeleteMixin, UserDeleteMixin
from ...core.permissions import UserPermissions


class CustomerCreate(BaseCustomerCreate):
    class Meta:
        description = "Creates a new customer."
        exclude = ["password"]
        model = models.User
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)


class CustomerUpdate(CustomerCreate):
    class Arguments:
        id = graphene.ID(description="ID of a customer to update.", required=True)
        input = CustomerInput(description="Fields required to update a customer.", required=True)

    class Meta:
        description = "Updates an existing customer."
        exclude = ["password"]
        model = models.User
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)

    @classmethod
    def generate_events(cls, info, old_instance: models.User, new_instance: models.User):
        # Retrieve the event base data
        staff_user = info.context.user
        new_email = new_instance.email
        new_fullname = new_instance.get_full_name()

        # Compare the data
        has_new_name = old_instance.get_full_name() != new_fullname
        has_new_email = old_instance.email != new_email

        # Generate the events accordingly
        if has_new_email:
            account_events.staff_user_assigned_email_to_a_customer_event(
                staff_user=staff_user, new_email=new_email
            )
        if has_new_name:
            account_events.staff_user_assigned_name_to_a_customer_event(
                staff_user=staff_user, new_name=new_fullname
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Generate events by comparing the old instance with the new data.

        It overrides the `perform_mutation` base method of ModelMutation.
        """

        # Retrieve the data
        original_instance = cls.get_instance(info, **data)
        data = data.get("input")

        # Clean the input and generate a new instance from the new data
        cleaned_input = cls.clean_input(info, original_instance, data)
        new_instance = cls.construct_instance(copy(original_instance), cleaned_input)

        # Save the new instance data
        cls.clean_instance(info, new_instance)
        cls.save(info, new_instance, cleaned_input)
        cls._save_m2m(info, new_instance, cleaned_input)

        # Generate events by comparing the instances
        cls.generate_events(info, original_instance, new_instance)

        # Return the response
        return cls.success_response(new_instance)


class UserDelete(UserDeleteMixin, ModelDeleteMutation):
    class Meta:
        abstract = True


class CustomerDelete(CustomerDeleteMixin, UserDelete):
    class Meta:
        description = "Deletes a customer."
        model = models.User
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a customer to delete.")

    @classmethod
    def perform_mutation(cls, root, info, **data):
        results = super().perform_mutation(root, info, **data)
        cls.post_process(info)
        return results


class AddressCreate(ModelMutation):
    user = graphene.Field(User, description="A user instance for which the address was created.")

    class Arguments:
        user_id = graphene.ID(description="ID of a user to create address for.", required=True)
        input = AddressInput(description="Fields required to create address.", required=True)

    class Meta:
        description = "Creates user address."
        model = models.Address
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user_id = data["user_id"]
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)
        response = super().perform_mutation(root, info, **data)
        if not response.errors:
            user.addresses.add(response.address)
            if not user.default_shipping_address:
                user.default_shipping_address = response.address
                user.save()
            response.user = user
        return response


class AddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address."
        model = models.Address
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)


class AddressDelete(BaseAddressDelete):
    class Meta:
        description = "Deletes an address."
        model = models.Address
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)


class AddressSetDefault(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        address_id = graphene.ID(required=True, description="ID of the address.")
        user_id = graphene.ID(
            required=True, description="ID of the user to change the address for."
        )

    class Meta:
        description = "Sets a default address for the given user."
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)

    @classmethod
    def perform_mutation(cls, _root, info, address_id, user_id, **data):
        address = cls.get_node_or_error(info, address_id, field="address_id", only_type=Address)
        user = cls.get_node_or_error(info, user_id, field="user_id", only_type=User)

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {"address_id": ValidationError("The address doesn't belong to that user.")}
            )

        if user.default_shipping_address:
            user.addresses.add(user.default_shipping_address)
        user.default_shipping_address = address
        user.save(update_fields=["default_shipping_address"])
        return cls(user=user)
