from django.db import models
from draftjs_sanitizer import clean_draft_js
from versatileimagefield.fields import PPOIField, VersatileImageField

from core.db.fields import SanitizedJSONField
from core.db.models import PublishableModel, SeoModel, SortableModel
from core.utils.images import UploadToPathAndRename
from ..core.permissions import ProductPermissions


class ProductType(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    has_variants = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        permissions = ((ProductPermissions.MANAGE_PRODUCT_TYPES.codename, "Manage product types"),)

    def __str__(self):
        return self.name


class Product(SeoModel, PublishableModel):
    supplier = models.ForeignKey(
        "suppliers.Supplier",
        related_name="products",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        "categories.Category",
        related_name="products",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    product_type = models.ForeignKey(
        "ProductType", related_name="products", on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    description = SanitizedJSONField(blank=True, default=dict, sanitizer=clean_draft_js)

    minimal_variant_price = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("name",)
        permissions = ((ProductPermissions.MANAGE_PRODUCTS.codename, "Manage products"),)


class ProductVariant(models.Model):
    product = models.ForeignKey("Product", related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField(max_length=255, unique=True)

    images = models.ManyToManyField("ProductImage", through="VariantImage")
    track_inventory = models.BooleanField(default=True)

    weight = models.PositiveIntegerField(default=0)

    cost = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=0)

    quantity = models.PositiveIntegerField(default=0)
    quantity_allocated = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sku",)

    def __str__(self):
        return self.sku


class ProductImage(SortableModel):
    product = models.ForeignKey("Product", related_name="images", on_delete=models.CASCADE)
    image = VersatileImageField(
        upload_to=UploadToPathAndRename(path="products", field="product.name"),
        ppoi_field="ppoi",
        blank=False,
    )
    ppoi = PPOIField()
    alt = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ("sort_order",)

    def get_ordering_queryset(self):
        return self.product.images.all()


class VariantImage(models.Model):
    variant = models.ForeignKey(
        "ProductVariant", related_name="variant_images", on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        ProductImage, related_name="variant_images", on_delete=models.CASCADE
    )
