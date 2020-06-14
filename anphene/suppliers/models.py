from django.contrib.postgres.fields import CICharField
from django.db import models

from ..core.permissions import SupplierPermissions
from ..users.models import PossiblePhoneNumberField


class Supplier(models.Model):
    name = CICharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    phone = PossiblePhoneNumberField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = ((SupplierPermissions.MANAGE_SUPPLIERS.codename, "Manage suppliers"),)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Always save the email as lowercase. Helps identifying unique email
        addresses.
        The de jure standard is that the local component of email addresses is
        case sensitive however the de facto standard is that they are not. In
        practice what happens is user confusion over why an email address
        entered with camel casing one day does not match an email address
        """
        if self.email:
            self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)
