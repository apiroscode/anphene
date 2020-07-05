import graphene

from .mutations import (
    AuthorizationKeyAdd,
    AuthorizationKeyDelete,
    ShopAddressUpdate,
    ShopDomainUpdate,
    ShopSettingsUpdate,
    StaffNotificationRecipientCreate,
    StaffNotificationRecipientDelete,
    StaffNotificationRecipientUpdate,
)
from .types import Shop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(Shop, description="Return information about the shop.", required=True)

    def resolve_shop(self, _info):
        return Shop()


class ShopMutations(graphene.ObjectType):
    authorization_key_add = AuthorizationKeyAdd.Field()
    authorization_key_delete = AuthorizationKeyDelete.Field()

    staff_notification_recipient_create = StaffNotificationRecipientCreate.Field()
    staff_notification_recipient_update = StaffNotificationRecipientUpdate.Field()
    staff_notification_recipient_delete = StaffNotificationRecipientDelete.Field()

    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_address_update = ShopAddressUpdate.Field()
