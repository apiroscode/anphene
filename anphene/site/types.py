import graphene
from django.conf import settings
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE

from core.decorators import permission_required
from core.graph.types import Permission
from core.utils import format_permissions_for_display
from . import models as site_models
from .enums import AuthorizationKeyType
from ..collections import models as collections_models
from ..collections.types import Collection
from ..core.permissions import get_permissions, SitePermissions
from ..menus.dataloaders import MenuByIdLoader
from ..menus.types import Menu
from ..users.types import Address


class Navigation(graphene.ObjectType):
    main = graphene.Field(Menu, description="Main navigation bar.")
    secondary = graphene.Field(Menu, description="Secondary navigation bar.")

    class Meta:
        description = "Represents shop's navigation menus."


class AuthorizationKey(graphene.ObjectType):
    name = AuthorizationKeyType(description="Name of the authorization backend.", required=True)
    key = graphene.String(description="Authorization key (client ID).", required=True)


class Domain(graphene.ObjectType):
    host = graphene.String(description="The host name of the domain.", required=True)
    ssl_enabled = graphene.Boolean(description="Inform if SSL is enabled.", required=True)
    url = graphene.String(description="Shop's absolute URL.", required=True)

    class Meta:
        description = "Represents shop's domain."


class Shop(graphene.ObjectType):
    # TODO: after order finish
    # available_payment_gateways = graphene.List(
    #     graphene.NonNull(PaymentGateway),
    #     description="List of available payment gateways.",
    #     required=True,
    # )
    authorization_keys = graphene.List(
        AuthorizationKey,
        description=(
            "List of configured authorization keys. Authorization keys are used to "
            "enable third-party OAuth authorization (currently Facebook or Google)."
        ),
        required=True,
    )
    default_mail_sender_name = graphene.String(description="Default shop's email sender's name.")
    default_mail_sender_address = graphene.String(
        description="Default shop's email sender's address."
    )
    description = graphene.String(description="Shop's description.")
    domain = graphene.Field(Domain, required=True, description="Shop's domain data.")
    homepage_collection = graphene.Field(
        Collection, description="Collection displayed on homepage."
    )
    name = graphene.String(description="Shop's name.", required=True)
    navigation = graphene.Field(Navigation, description="Shop's navigation.")
    permissions = graphene.List(
        Permission, description="List of available permissions.", required=True
    )
    phone_prefixes = graphene.List(
        graphene.String, description="List of possible phone prefixes.", required=True
    )
    header_text = graphene.String(description="Header text.")
    track_inventory_by_default = graphene.Boolean(description="Enable inventory tracking.")

    company_address = graphene.Field(Address, description="Company address.", required=False)
    customer_set_password_url = graphene.String(
        description="URL of a view where customers can set their password.", required=False,
    )

    # TODO:
    # staff_notification_recipients = graphene.List(
    #     StaffNotificationRecipient,
    #     description="List of staff notification recipients.",
    #     required=False,
    # )

    class Meta:
        description = "Represents a shop resource containing general shop data and configuration."

    #
    # @staticmethod
    # def resolve_available_payment_gateways(_, _info):
    #     return [gtw for gtw in get_plugins_manager().list_payment_gateways()]

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_authorization_keys(_, _info):
        return site_models.AuthorizationKey.objects.all()

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_mail_sender_name(_, info):
        return info.context.site.settings.default_mail_sender_name

    @staticmethod
    @permission_required(SitePermissions.MANAGE_SETTINGS)
    def resolve_default_mail_sender_address(_, info):
        return info.context.site.settings.default_mail_sender_address

    @staticmethod
    def resolve_description(_, info):
        return info.context.site.settings.description

    @staticmethod
    def resolve_domain(_, info):
        site = info.context.site
        return Domain(
            host=site.domain,
            ssl_enabled=settings.ENABLE_SSL,
            url=info.context.build_absolute_uri("/"),
        )

    @staticmethod
    def resolve_homepage_collection(_, info):
        collection_pk = info.context.site.settings.homepage_collection_id
        qs = collections_models.Collection.objects.all()
        return qs.filter(pk=collection_pk).first()

    @staticmethod
    def resolve_name(_, info):
        return info.context.site.name

    @staticmethod
    def resolve_navigation(_, info):
        site_settings = info.context.site.settings
        main = (
            MenuByIdLoader(info.context).load(site_settings.top_menu_id)
            if site_settings.top_menu_id
            else None
        )
        secondary = (
            MenuByIdLoader(info.context).load(site_settings.bottom_menu_id)
            if site_settings.bottom_menu_id
            else None
        )
        return Navigation(main=main, secondary=secondary)

    @staticmethod
    def resolve_permissions(_, _info):
        permissions = get_permissions()
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_phone_prefixes(_, _info):
        return list(COUNTRY_CODE_TO_REGION_CODE.keys())

    @staticmethod
    def resolve_header_text(_, info):
        return info.context.site.settings.header_text

    @staticmethod
    def resolve_track_inventory_by_default(_, info):
        return info.context.site.settings.track_inventory_by_default

    @staticmethod
    def resolve_company_address(_, info):
        return info.context.site.settings.company_address

    @staticmethod
    def resolve_customer_set_password_url(_, info):
        return info.context.site.settings.customer_set_password_url

    # TODO:
    # @staticmethod
    # @permission_required(SitePermissions.MANAGE_SETTINGS)
    # def resolve_staff_notification_recipients(_, info):
    #     return account_models.StaffNotificationRecipient.objects.all()
