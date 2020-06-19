from django.contrib.postgres.fields import CICharField
from django.db import models
from django.db.models import F
from django.utils.encoding import smart_text
from draftjs_sanitizer import clean_draft_js
from mptt.models import MPTTModel
from versatileimagefield.fields import PPOIField, VersatileImageField

from core.db.fields import SanitizedJSONField
from core.db.models import PublishableModel, SeoModel, SortableModel
from core.utils.images import UploadToPathAndRename
from .managers import ProductsQueryset, ProductVariantQueryset
from ..core.permissions import ProductPermissions
from ..discounts.utils import calculate_discounted_price
from ..core.data import MoneyRange


class ProductType(models.Model):
    name = CICharField(max_length=250, unique=True)
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

    objects = ProductsQueryset.as_manager()

    class Meta:
        ordering = ("name",)
        permissions = ((ProductPermissions.MANAGE_PRODUCTS.codename, "Manage products"),)

    def __iter__(self):
        if not hasattr(self, "__variants"):
            setattr(self, "__variants", self.variants.all())
        return iter(getattr(self, "__variants"))

    def __repr__(self) -> str:
        class_ = type(self)
        return "<%s.%s(pk=%r, name=%r)>" % (
            class_.__module__,
            class_.__name__,
            self.pk,
            self.name,
        )

    def __str__(self) -> str:
        return self.name

    def get_first_image(self):
        images = list(self.images.all())
        return images[0] if images else None

    def get_price_range(self, discounts=None):
        prices = [variant.get_price(discounts) for variant in self]
        return MoneyRange(min(prices), max(prices))

    @staticmethod
    def sort_by_attribute_fields() -> list:
        return ["concatenated_values_order", "concatenated_values", "name"]


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

    objects = ProductVariantQueryset.as_manager()

    class Meta:
        ordering = ("sku",)

    def __str__(self):
        return self.sku

    @property
    def is_visible(self) -> bool:
        return self.product.is_visible

    def get_price(self, discounts):
        return calculate_discounted_price(
            product=self.product,
            price=self.price,
            collections=self.product.collections.all(),
            discounts=discounts,
        )

    def display_product(self) -> str:
        variant_display = str(self)
        product = self.product
        product_display = f"{product} ({variant_display})" if variant_display else str(product)
        return smart_text(product_display)

    def get_first_image(self) -> "ProductImage":
        images = list(self.images.all())
        return images[0] if images else self.product.get_first_image()

    def increase_stock(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_stock(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])


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
