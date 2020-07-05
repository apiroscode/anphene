from . import models
from ..core.permissions import PagePermissions


def resolve_pages(info, **_kwargs):
    user = info.context.user
    return models.Page.objects.visible_to_user(user, PagePermissions.MANAGE_PAGES)
