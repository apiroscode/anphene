from enum import Enum

from django.contrib.auth.models import Permission


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]


class UserPermissions(BasePermissionEnum):
    MANAGE_CUSTOMERS = "users.manage_customers"
    MANAGE_STAFF = "users.manage_staff"


class GroupPermissions(BasePermissionEnum):
    MANAGE_GROUPS = "users.manage_groups"


class SitePermissions(BasePermissionEnum):
    MANAGE_SETTINGS = "site.manage_settings"


PERMISSIONS_ENUMS = [UserPermissions, GroupPermissions, SitePermissions]


def split_permission_codename(permissions):
    return [permission.split(".")[1] for permission in permissions]


def get_permissions_codename():
    permissions_values = [
        enum.codename for permission_enum in PERMISSIONS_ENUMS for enum in permission_enum
    ]
    return permissions_values


def get_permissions_enum_list():
    permissions_list = [
        (enum.name, enum.value)
        for permission_enum in PERMISSIONS_ENUMS
        for enum in permission_enum
    ]
    return permissions_list


def get_permissions(permissions=None):
    if permissions is None:
        codenames = get_permissions_codename()
    else:
        codenames = split_permission_codename(permissions)
    return (
        Permission.objects.filter(codename__in=codenames)
        .prefetch_related("content_type")
        .order_by("codename")
    )
