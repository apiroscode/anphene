from django.contrib.auth.models import Permission
from django.db.models import Value
from django.db.models.functions import Concat

from ..core.permissions import get_permissions


def get_user_permissions(user):
    """Return all user permissions - from user groups and user_permissions field."""
    if user.is_superuser:
        return get_permissions()
    groups = user.groups.all()
    user_permissions = user.user_permissions.all()
    group_permissions = Permission.objects.filter(group__in=groups)
    permissions = user_permissions | group_permissions
    return permissions


def get_group_permission_codes(group):
    """Return group permissions in the format '<app label>.<permission codename>'."""
    return group.permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("formated_codename", flat=True)
