import graphene
from django.contrib.auth import models as auth_models

from core.exceptions import PermissionDenied
from core.utils import format_permissions_for_display
from . import models
from .utils import get_user_permissions
from ..core.permissions import get_permissions, UserPermissions


def resolve_address(info, id):
    user = info.context.user
    _model, address_pk = graphene.Node.from_global_id(id)

    if user and not user.is_anonymous:
        return user.addresses.filter(id=address_pk).first()
    return PermissionDenied()


def resolve_all_permissions(_info, **_kwargs):
    return format_permissions_for_display(get_permissions())


def resolve_permissions(root: models.User):
    permissions = get_user_permissions(root)
    permissions = permissions.prefetch_related("content_type").order_by("codename")
    return format_permissions_for_display(permissions)


def resolve_groups(_info, **_kwargs):
    qs = auth_models.Group.objects.all()
    return qs


def resolve_customers(_info, **_kwargs):
    qs = models.User.objects.customers()
    return qs.distinct()


def resolve_staff_users(info, **_kwargs):
    user = info.context.user
    qs = models.User.objects.staff().exclude(id=user.id)
    return qs.distinct()


def resolve_user(info, id):
    user = info.context.user
    if user:
        _model, user_pk = graphene.Node.from_global_id(id)
        if user.has_perms([UserPermissions.MANAGE_STAFF, UserPermissions.MANAGE_CUSTOMERS]):
            return models.User.objects.exclude(id=user.id).filter(pk=user_pk).first()
        if user.has_perm(UserPermissions.MANAGE_STAFF):
            return models.User.objects.staff().exclude(id=user.id).filter(pk=user_pk).first()
        if user.has_perm(UserPermissions.MANAGE_CUSTOMERS):
            return models.User.objects.customers().filter(pk=user_pk).first()
    return PermissionDenied()
