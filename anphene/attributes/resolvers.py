from . import models
from ..core.permissions import AttributePermissions


def resolve_attributes(info, **_kwargs):
    qs = models.Attribute.objects.get_visible_to_user(
        info.context.user, AttributePermissions.MANAGE_ATTRIBUTES
    )

    return qs.distinct()
