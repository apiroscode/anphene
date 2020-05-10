from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CIEmailField
from django.db import models
from django.db.models import CharField
from django.utils.translation import ugettext_lazy as _

from anphene.utils.permissions import UserPermissions


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    REQUIRED_FIELDS = []

    # Based
    email = CIEmailField(unique=True)
    USERNAME_FIELD = "email"

    # STAFF
    name = CharField(_("Name of User"), blank=True, max_length=255)
    id_card = models.ImageField(upload_to="staff/id_card/", blank=True)

    # CUSTOMER
    balance = models.PositiveIntegerField(default=0)

    class Meta:
        permissions = (
            (UserPermissions.MANAGE_CUSTOMERS.codename, "Manage customers."),
            (UserPermissions.MANAGE_STAFF.codename, "Manage staff."),
        )

    def save(self, *args, **kwargs):
        """
        Always save the email as lowercase. Helps identifying unique email
        addresses.
        The de jure standard is that the local component of email addresses is
        case sensitive however the de facto standard is that they are not. In
        practice what happens is user confusion over why an email address
        entered with camel casing one day does not match an email address
        """
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm, obj=None):  # type: ignore
        # This method is overridden to accept perm as BasePermissionEnum
        return super().has_perm(perm.value, obj)
