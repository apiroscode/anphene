from email.headerregistry import Address
from email.utils import parseaddr
from typing import Optional

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import models

from . import AuthenticationBackends
from .patch_sites import patch_contrib_sites
from ..core.permissions import SitePermissions

patch_contrib_sites()


def email_sender_name_validators():
    return [
        RegexValidator(r"[\n\r]", inverse_match=True, message="New lines are not allowed."),
        MaxLengthValidator(78),
    ]


class SiteSettings(models.Model):
    site = models.OneToOneField(Site, related_name="settings", on_delete=models.CASCADE)
    header_text = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    top_menu = models.ForeignKey(
        "menus.Menu", on_delete=models.SET_NULL, related_name="+", blank=True, null=True
    )
    bottom_menu = models.ForeignKey(
        "menus.Menu", on_delete=models.SET_NULL, related_name="+", blank=True, null=True
    )
    track_inventory_by_default = models.BooleanField(default=True)
    homepage_collection = models.ForeignKey(
        "collections.Collection",
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )
    company_address = models.ForeignKey(
        "users.Address", blank=True, null=True, on_delete=models.SET_NULL
    )
    default_mail_sender_name = models.CharField(
        max_length=78, blank=True, default="", validators=email_sender_name_validators()
    )
    default_mail_sender_address = models.EmailField(blank=True)
    customer_set_password_url = models.CharField(max_length=255, blank=True)

    class Meta:
        permissions = ((SitePermissions.MANAGE_SETTINGS.codename, "Manage settings"),)

    def __str__(self):
        return self.site.name

    @property
    def default_from_email(self) -> str:
        sender_name: str = self.default_mail_sender_name
        sender_address: Optional[str] = self.default_mail_sender_address

        if not sender_address:
            sender_address = settings.DEFAULT_FROM_EMAIL

            if not sender_address:
                raise ImproperlyConfigured("No sender email address has been set-up")

            sender_name, sender_address = parseaddr(sender_address)

        # Note: we only want to format the address in accordance to RFC 5322
        # but our job is not to sanitize the values. The sanitized value, encoding, etc.
        # will depend on the email backend being used.
        #
        # Refer to email.header.Header and django.core.mail.message.sanitize_address.
        value = str(Address(sender_name, addr_spec=sender_address))
        return value

    def available_backends(self):
        return self.authorizationkey_set.values_list("name", flat=True)


class AuthorizationKey(models.Model):
    site_settings = models.ForeignKey(SiteSettings, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, choices=AuthenticationBackends.BACKENDS)
    key = models.TextField()
    password = models.TextField()

    class Meta:
        unique_together = (("site_settings", "name"),)

    def __str__(self):
        return self.name

    def key_and_secret(self):
        return self.key, self.password
