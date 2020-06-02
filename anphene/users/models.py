from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CIEmailField, JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import CharField, Q, Value
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.modelfields import PhoneNumber, PhoneNumberField

from anphene.core.permissions import GroupPermissions, UserPermissions
from anphene.regions.models import SubDistrict
from . import CustomerEvents
from .validators import validate_possible_number


class PossiblePhoneNumberField(PhoneNumberField):
    """Less strict field for phone numbers written to database."""

    default_validators = [validate_possible_number]


class AddressQueryset(models.QuerySet):
    def annotate_default(self, user):
        # Set default shipping/billing address pk to None
        # if default shipping/billing address doesn't exist
        default_shipping_address_pk = None
        if user.default_shipping_address:
            default_shipping_address_pk = user.default_shipping_address.pk

        return user.addresses.annotate(
            user_default_shipping_address_pk=Value(
                default_shipping_address_pk, models.IntegerField()
            )
        )


class Address(models.Model):
    company_name = models.CharField(max_length=256, blank=True)
    name = models.CharField(max_length=256, blank=True)
    phone = PossiblePhoneNumberField(blank=True, default="")
    street_address = models.CharField(max_length=256)
    postal_code = models.CharField(max_length=20)
    sub_district = models.ForeignKey(SubDistrict, on_delete=models.CASCADE)

    objects = AddressQueryset.as_manager()

    class Meta:
        ordering = ["pk"]

    @property
    def full_name(self):
        return self.name

    def __str__(self):
        if self.company_name:
            return "%s - %s" % (self.company_name, self.full_name)
        return self.full_name

    def __eq__(self, other):
        if not isinstance(other, Address):
            return False
        return self.as_data() == other.as_data()

    def as_data(self):
        """Return the address as a dict suitable for passing as kwargs.

        Result does not contain the primary key or an associated user.
        """
        data = model_to_dict(self, exclude=["id", "user"])
        if isinstance(data["phone"], PhoneNumber):
            data["phone"] = data["phone"].as_e164
        return data

    def get_copy(self):
        """Return a new instance of the same address."""
        return Address.objects.create(**self.as_data())


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_staff=False, is_active=True, **extra_fields):
        """Create a user instance with the given email and password."""
        email = UserManager.normalize_email(email).lower()
        # Google OAuth2 backend send unnecessary username field
        extra_fields.pop("username", None)

        user = self.model(email=email, is_active=is_active, is_staff=is_staff, **extra_fields)
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        return self.create_user(email, password, is_staff=True, is_superuser=True, **extra_fields)

    def customers(self):
        return self.get_queryset().filter(
            Q(is_staff=False) | (Q(is_staff=True) & Q(orders__isnull=False))
        )

    def staff(self):
        return self.get_queryset().filter(is_staff=True, is_superuser=False)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    REQUIRED_FIELDS = []

    # STAFF
    name = CharField(_("Name of User"), blank=True, max_length=255)
    id_card = models.ImageField(upload_to="staff/id_card/", blank=True)

    # CUSTOMER
    addresses = models.ManyToManyField(Address, blank=True, related_name="user_addresses")
    default_shipping_address = models.ForeignKey(
        Address, related_name="+", null=True, blank=True, on_delete=models.SET_NULL
    )
    balance = models.PositiveIntegerField(default=0)

    # Based
    email = CIEmailField(unique=True)
    note = models.TextField(null=True, blank=True)
    USERNAME_FIELD = "email"
    objects = UserManager()

    class Meta:
        permissions = (
            (UserPermissions.MANAGE_CUSTOMERS.codename, "Manage customers"),
            (UserPermissions.MANAGE_STAFF.codename, "Manage staff"),
            (GroupPermissions.MANAGE_GROUPS.codename, "Manage groups"),
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


class CustomerNote(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(db_index=True, auto_now_add=True)
    content = models.TextField()
    is_public = models.BooleanField(default=True)
    customer = models.ForeignKey(User, related_name="notes", on_delete=models.CASCADE)

    class Meta:
        ordering = ("date",)


class CustomerEvent(models.Model):
    """Model used to store events that happened during the customer lifecycle."""

    date = models.DateTimeField(default=timezone.now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[(type_name.upper(), type_name) for type_name, _ in CustomerEvents.CHOICES],
    )

    # TODO: AFTER ORDER COMPLETED
    # order = models.ForeignKey("order.Order", on_delete=models.SET_NULL, null=True)
    parameters = JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)

    user = models.ForeignKey(User, related_name="events", on_delete=models.CASCADE)

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"


class StaffNotificationRecipient(models.Model):
    user = models.OneToOneField(
        User, related_name="staff_notification", on_delete=models.CASCADE, blank=True, null=True
    )
    staff_email = models.EmailField(unique=True, blank=True, null=True)
    active = models.BooleanField(default=True)

    def get_email(self):
        return self.user.email if self.user else self.staff_email
