from enum import Enum

from django.contrib.auth.models import Permission


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]


class UserPermissions(BasePermissionEnum):
    MANAGE_CUSTOMERS = "users.manage_customers"
    MANAGE_STAFF = "users.manage_staff"
