from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models


class Checkout(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(auto_now=True)

    token = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        "users.User", blank=True, null=True, related_name="checkouts", on_delete=models.CASCADE,
    )
    shipping_address = models.ForeignKey(
        "users.Address", related_name="+", editable=False, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ("-last_change", "pk")

    def get_total_weight(self):
        return sum([line.variant.weight * line.quantity for line in self.lines.all()])


class CheckoutLine(models.Model):
    checkout = models.ForeignKey(Checkout, related_name="lines", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        "products.ProductVariant", related_name="+", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("checkout", "variant")
        ordering = ("id",)
