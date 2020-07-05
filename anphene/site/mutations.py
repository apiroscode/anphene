import graphene
from django.core.exceptions import ValidationError

from core.graph.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from core.utils.urls import validate_storefront_url
from . import models as site_models
from .types import AuthorizationKey, AuthorizationKeyType, Shop
from ..core.permissions import SitePermissions
from ..users import models as users_models


class ShopAddressInput(graphene.InputObjectType):
    name = graphene.String(description="Company or organization.")
    phone = graphene.String(description="Phone number.")
    street_address = graphene.String(description="Address.")
    postal_code = graphene.String(description="Postal code.")
    sub_district = graphene.ID(description="District id.")


class ShopSettingsInput(graphene.InputObjectType):
    header_text = graphene.String(description="Header text.")
    description = graphene.String(description="SEO description.")
    track_inventory_by_default = graphene.Boolean(description="Enable inventory tracking.")
    default_mail_sender_name = graphene.String(description="Default email sender's name.")
    default_mail_sender_address = graphene.String(description="Default email sender's address.")
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password."
    )


class SiteDomainInput(graphene.InputObjectType):
    name = graphene.String(description="Shop site name.")
    domain = graphene.String(description="Domain name for shop.")


class ShopSettingsUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = ShopSettingsInput(
            description="Fields required to update shop settings.", required=True
        )

    class Meta:
        description = "Updates shop settings."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    @classmethod
    def clean_input(cls, _info, _instance, data):
        if data.get("customer_set_password_url"):
            try:
                validate_storefront_url(data["customer_set_password_url"])
            except ValidationError as error:
                raise ValidationError({"customer_set_password_url": error})
        return data

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        for field_name, desired_value in cleaned_data.items():
            current_value = getattr(instance, field_name)
            if current_value != desired_value:
                setattr(instance, field_name, desired_value)
        return instance

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = info.context.site.settings
        data = data.get("input")
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        instance.save()
        return ShopSettingsUpdate(shop=Shop())


class ShopAddressUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = ShopAddressInput(description="Fields required to update shop address.")

    class Meta:
        description = (
            "Update the shop's address. If the `null` value is passed, the currently "
            "selected address will be deleted."
        )
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site_settings = info.context.site.settings
        data = data.get("input")
        if data:
            if not site_settings.company_address:
                company_address = users_models.Address()
            else:
                company_address = site_settings.company_address
            data["sub_district"] = cls.get_node_or_error(info, data["sub_district"])
            company_address = cls.construct_instance(company_address, data)
            cls.clean_instance(info, company_address)
            company_address.save()
            site_settings.company_address = company_address
            site_settings.save(update_fields=["company_address"])
        else:
            if site_settings.company_address:
                site_settings.company_address.delete()
        return ShopAddressUpdate(shop=Shop())


class ShopDomainUpdate(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        input = SiteDomainInput(description="Fields required to update site.")

    class Meta:
        description = "Updates site domain of the shop."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        site = info.context.site
        data = data.get("input")
        domain = data.get("domain")
        name = data.get("name")
        if domain is not None:
            site.domain = domain
        if name is not None:
            site.name = name
        cls.clean_instance(info, site)
        site.save()
        return ShopDomainUpdate(shop=Shop())


class AuthorizationKeyInput(graphene.InputObjectType):
    key = graphene.String(required=True, description="Client authorization key (client ID).")
    password = graphene.String(required=True, description="Client secret.")


class AuthorizationKeyAdd(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description="Newly added authorization key."
    )
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Adds an authorization key."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    class Arguments:
        key_type = AuthorizationKeyType(
            required=True, description="Type of an authorization key to add."
        )
        input = AuthorizationKeyInput(
            required=True, description="Fields required to create an authorization key."
        )

    @classmethod
    def perform_mutation(cls, _root, info, key_type, **data):
        if site_models.AuthorizationKey.objects.filter(name=key_type).exists():
            raise ValidationError(
                {"key_type": ValidationError("Authorization key already exists.")}
            )

        site_settings = info.context.site.settings
        instance = site_models.AuthorizationKey(
            name=key_type, site_settings=site_settings, **data.get("input")
        )
        cls.clean_instance(info, instance)
        instance.save()
        return AuthorizationKeyAdd(authorization_key=instance, shop=Shop())


class AuthorizationKeyDelete(BaseMutation):
    authorization_key = graphene.Field(
        AuthorizationKey, description="Authorization key that was deleted."
    )
    shop = graphene.Field(Shop, description="Updated shop.")

    class Arguments:
        key_type = AuthorizationKeyType(required=True, description="Type of a key to delete.")

    class Meta:
        description = "Deletes an authorization key."
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    @classmethod
    def perform_mutation(cls, _root, info, key_type):
        try:
            site_settings = info.context.site.settings
            instance = site_models.AuthorizationKey.objects.get(
                name=key_type, site_settings=site_settings
            )
        except site_models.AuthorizationKey.DoesNotExist:
            raise ValidationError(
                {"key_type": ValidationError("Couldn't resolve authorization key")}
            )

        instance.delete()
        return AuthorizationKeyDelete(authorization_key=instance, shop=Shop())


class StaffNotificationRecipientInput(graphene.InputObjectType):
    user = graphene.ID(
        required=False, description="The ID of the user subscribed to email notifications..",
    )
    email = graphene.String(
        required=False, description="Email address of a user subscribed to email notifications.",
    )
    active = graphene.Boolean(required=False, description="Determines if a notification active.")


class StaffNotificationRecipientCreate(ModelMutation):
    class Arguments:
        input = StaffNotificationRecipientInput(
            required=True, description="Fields required to create a staff notification recipient.",
        )

    class Meta:
        description = "Creates a new staff notification recipient."
        model = users_models.StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_input(instance, cleaned_input)
        email = cleaned_input.pop("email", None)
        if email:
            staff_user = users_models.User.objects.filter(email=email).first()
            if staff_user:
                cleaned_input["user"] = staff_user
            else:
                cleaned_input["staff_email"] = email
        return cleaned_input

    @staticmethod
    def validate_input(instance, cleaned_input):
        email = cleaned_input.get("email")
        user = cleaned_input.get("user")
        if not email and not user:
            if instance.id and "user" in cleaned_input or "email" in cleaned_input:
                raise ValidationError(
                    {"staff_notification": ValidationError("User and email cannot be set empty")}
                )
            if not instance.id:
                raise ValidationError(
                    {"staff_notification": ValidationError("User or email is required")}
                )
        if user and not user.is_staff:
            raise ValidationError({"user": ValidationError("User has to be staff user")})


class StaffNotificationRecipientUpdate(StaffNotificationRecipientCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to update."
        )
        input = StaffNotificationRecipientInput(
            required=True, description="Fields required to update a staff notification recipient.",
        )

    class Meta:
        description = "Updates a staff notification recipient."
        model = users_models.StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)


class StaffNotificationRecipientDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a staff notification recipient to delete."
        )

    class Meta:
        description = "Delete staff notification recipient."
        model = users_models.StaffNotificationRecipient
        permissions = (SitePermissions.MANAGE_SETTINGS,)
