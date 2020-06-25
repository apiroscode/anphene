from django.db import models

from core.db.models import SortableModel
from . import AttributeInputType
from .managers import AttributeQuerySet
from ..core.permissions import AttributePermissions


class Attribute(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=250, unique=True)

    input_type = models.CharField(
        max_length=50, choices=AttributeInputType.CHOICES, default=AttributeInputType.DROPDOWN,
    )

    product_types = models.ManyToManyField(
        "products.ProductType",
        blank=True,
        related_name="product_attributes",
        through="AttributeProduct",
        through_fields=("attribute", "product_type"),
    )
    product_variant_types = models.ManyToManyField(
        "products.ProductType",
        blank=True,
        related_name="variant_attributes",
        through="AttributeVariant",
        through_fields=("attribute", "product_type"),
    )

    value_required = models.BooleanField(default=False, blank=True)
    visible_in_storefront = models.BooleanField(default=True, blank=True)

    filterable_in_storefront = models.BooleanField(default=True, blank=True)
    filterable_in_dashboard = models.BooleanField(default=True, blank=True)

    storefront_search_position = models.IntegerField(default=0, blank=True)
    available_in_grid = models.BooleanField(default=True, blank=True)

    objects = AttributeQuerySet.as_manager()

    class Meta:
        ordering = ("storefront_search_position", "slug")
        permissions = ((AttributePermissions.MANAGE_ATTRIBUTES.codename, "Manage attributes"),)

    def __str__(self):
        return self.name

    def has_values(self):
        return self.values.exists()


class AttributeValue(SortableModel):
    attribute = models.ForeignKey(Attribute, related_name="values", on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    value = models.CharField(max_length=100, blank=True, default="")
    slug = models.SlugField(max_length=255)

    class Meta:
        ordering = ("sort_order", "id")
        unique_together = ("slug", "attribute")

    def __str__(self):
        return self.name

    @property
    def input_type(self):
        return self.attribute.input_type

    def get_ordering_queryset(self):
        return self.attribute.values.all()


class AttributeProduct(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributeproduct", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        "products.ProductType", related_name="attributeproduct", on_delete=models.CASCADE
    )
    assigned_products = models.ManyToManyField(
        "products.Product",
        blank=True,
        through="AssignedProductAttribute",
        through_fields=("assignment", "product"),
        related_name="attributesrelated",
    )

    class Meta:
        unique_together = (("attribute", "product_type"),)
        ordering = ("sort_order",)

    def get_ordering_queryset(self):
        return self.product_type.attributeproduct.all()


class AttributeVariant(SortableModel):
    attribute = models.ForeignKey(
        "Attribute", related_name="attributevariant", on_delete=models.CASCADE
    )
    product_type = models.ForeignKey(
        "products.ProductType", related_name="attributevariant", on_delete=models.CASCADE
    )
    assigned_variants = models.ManyToManyField(
        "products.ProductVariant",
        blank=True,
        through="AssignedVariantAttribute",
        through_fields=("assignment", "variant"),
        related_name="attributesrelated",
    )

    class Meta:
        unique_together = (("attribute", "product_type"),)
        ordering = ("sort_order",)

    def get_ordering_queryset(self):
        return self.product_type.attributevariant.all()


class AssignedProductAttribute(models.Model):
    """Associate a product type attribute and selected values to a given product."""

    product = models.ForeignKey(
        "products.Product", related_name="attributes", on_delete=models.CASCADE
    )
    assignment = models.ForeignKey(
        "AttributeProduct", on_delete=models.CASCADE, related_name="productassignments"
    )
    values = models.ManyToManyField("AttributeValue")

    class Meta:
        unique_together = (("product", "assignment"),)

    @property
    def attribute(self):
        return self.assignment.attribute

    @property
    def attribute_pk(self):
        return self.assignment.attribute_id


class AssignedVariantAttribute(models.Model):
    """Associate a product type attribute and selected values to a given variant."""

    variant = models.ForeignKey(
        "products.ProductVariant", related_name="attributes", on_delete=models.CASCADE
    )
    assignment = models.ForeignKey(
        "AttributeVariant", on_delete=models.CASCADE, related_name="variantassignments"
    )
    values = models.ManyToManyField("AttributeValue")

    class Meta:
        unique_together = (("variant", "assignment"),)

    @property
    def attribute(self):
        return self.assignment.attribute

    @property
    def attribute_pk(self):
        return self.assignment.attribute_id
