from . import models
from ..core.permissions import CollectionPermissions


def resolve_collections(info, **_kwargs):
    user = info.context.user
    return models.Collection.objects.visible_to_user(
        user, CollectionPermissions.MANAGE_COLLECTIONS
    )
