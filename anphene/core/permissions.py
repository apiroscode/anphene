from enum import Enum

from django.contrib.auth.models import Permission


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]


class AttributePermissions(BasePermissionEnum):
    MANAGE_ATTRIBUTES = "attributes.manage_attributes"


class CategoryPermissions(BasePermissionEnum):
    MANAGE_CATEGORIES = "categories.manage_categories"


class CollectionPermissions(BasePermissionEnum):
    MANAGE_COLLECTIONS = "collections.manage_collections"


class GroupPermissions(BasePermissionEnum):
    MANAGE_GROUPS = "users.manage_groups"


class ProductPermission(BasePermissionEnum):
    MANAGE_PRODUCTS = "products.manage_products"
    MANAGE_PRODUCT_TYPES = "products.manage_product_types"


class SitePermissions(BasePermissionEnum):
    MANAGE_SETTINGS = "site.manage_settings"


class SupplierPermissions(BasePermissionEnum):
    MANAGE_SUPPLIERS = "suppliers.manage_suppliers"


class UserPermissions(BasePermissionEnum):
    MANAGE_CUSTOMERS = "users.manage_customers"
    MANAGE_STAFF = "users.manage_staff"


PERMISSIONS_ENUMS = [
    AttributePermissions,
    CategoryPermissions,
    CollectionPermissions,
    GroupPermissions,
    ProductPermission,
    SitePermissions,
    SupplierPermissions,
    UserPermissions,
]


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
