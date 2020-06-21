from decimal import Decimal

from django.contrib.postgres.fields import CICharField
from django.db import models
from django.utils import timezone

from . import DiscountType, VoucherType
from .managers import SaleQueryset, VoucherQueryset
from ..core.permissions import DiscountPermissions


def get_discount(discount_type, value, price):
    after_discount = 0
    if discount_type == DiscountType.FIXED:
        after_discount = price - value
    elif discount_type == DiscountType.PERCENTAGE:
        after_discount = price - (Decimal(value) / 100 * price)

    if after_discount <= 0:
        return price

    return round(price - after_discount)


class NotApplicable(ValueError):
    """Exception raised when a discount is not applicable to a checkout.

    The error is raised if the order value is below the minimum required
    price or the order quantity is below the minimum quantity of items.
    Minimum price will be available as the `min_spent` attribute.
    Minimum quantity will be available as the `min_checkout_items_quantity` attribute.
    """

    def __init__(self, msg, min_spent=None, min_checkout_items_quantity=None):
        super().__init__(msg)
        self.min_spent = min_spent
        self.min_checkout_items_quantity = min_checkout_items_quantity


class Voucher(models.Model):
    type = models.CharField(
        max_length=20, choices=VoucherType.CHOICES, default=VoucherType.ENTIRE_ORDER
    )
    code = CICharField(max_length=12, unique=True, db_index=True)
    usage_limit = models.PositiveIntegerField(default=0)
    used = models.PositiveIntegerField(default=0, editable=False)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    # this field indicates if discount should be applied per order or
    # individually to every item
    apply_once_per_order = models.BooleanField(default=False)
    apply_once_per_customer = models.BooleanField(default=False)

    discount_type = models.CharField(
        max_length=10, choices=DiscountType.CHOICES, default=DiscountType.FIXED
    )
    discount_value = models.PositiveIntegerField(default=0)

    min_spent_amount = models.PositiveIntegerField(default=0)
    min_checkout_items_quantity = models.PositiveIntegerField(default=0)

    products = models.ManyToManyField("products.Product", blank=True)
    collections = models.ManyToManyField("collections.Collection", blank=True)
    categories = models.ManyToManyField("categories.Category", blank=True)

    objects = VoucherQueryset.as_manager()

    class Meta:
        ordering = ("code",)
        permissions = (
            (DiscountPermissions.MANAGE_DISCOUNTS.codename, "Manage sales and vouchers.",),
        )

    def __str__(self):
        if self.name:
            return self.name
        discount = "%s %s" % (self.discount_value, self.get_discount_type_display(),)
        if self.type == VoucherType.SHIPPING:
            if self.is_free:
                return "Free shipping"
            return f"{discount} off shipping"
        if self.type == VoucherType.SPECIFIC_PRODUCT:
            return f"%{discount} off specific products"
        return f"{discount} off"

    @property
    def is_free(self):
        return (
            self.discount_value == Decimal(100) and self.discount_type == DiscountType.PERCENTAGE
        )

    def get_discount(self, price):
        return get_discount(self.discount_type, self.discount_value, price)

    def validate_min_spent(self, value):
        if self.min_spent_amount and value < self.min_spent_amount:
            msg = f"This offer is only valid for orders over {self.min_spent_amount}."
            raise NotApplicable(msg, min_spent=self.min_spent_amount)

    def validate_min_checkout_items_quantity(self, quantity):
        min_checkout_items_quantity = self.min_checkout_items_quantity
        if min_checkout_items_quantity and min_checkout_items_quantity > quantity:
            msg = (
                "This offer is only valid for orders with a minimum of "
                f"{min_checkout_items_quantity} quantity."
            )
            raise NotApplicable(
                msg, min_checkout_items_quantity=min_checkout_items_quantity,
            )

    def validate_once_per_customer(self, customer_email):
        voucher_customer = VoucherCustomer.objects.filter(
            voucher=self, customer_email=customer_email
        )
        if voucher_customer:
            msg = "This offer is valid only once per customer."
            raise NotApplicable(msg)


class VoucherCustomer(models.Model):
    voucher = models.ForeignKey(Voucher, related_name="customers", on_delete=models.CASCADE)
    customer_email = models.EmailField()

    class Meta:
        ordering = ("voucher", "customer_email")
        unique_together = (("voucher", "customer_email"),)


class Sale(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=10, choices=DiscountType.CHOICES, default=DiscountType.FIXED,
    )
    value = models.PositiveIntegerField(default=0)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    products = models.ManyToManyField("products.Product", blank=True)
    categories = models.ManyToManyField("categories.Category", blank=True)
    collections = models.ManyToManyField("collections.Collection", blank=True)

    objects = SaleQueryset.as_manager()

    class Meta:
        ordering = ("name", "pk")

    def __repr__(self):
        return "Sale(name=%r, value=%r, type=%s)" % (
            str(self.name),
            self.value,
            self.get_type_display(),
        )

    def __str__(self):
        return self.name

    def get_discount(self, price):
        return get_discount(self.type, self.value, price)
