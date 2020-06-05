from django.contrib.postgres.fields import CICharField, JSONField
from django.db import models
from versatileimagefield.fields import VersatileImageField

from core.db.models import PublishableModel, SeoModel, SortableModel
from core.utils.images import UploadToPathAndRename
from ..core.permissions import CollectionPermissions


class Collection(SeoModel, PublishableModel):
    name = CICharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    products = models.ManyToManyField(
        "products.Product",
        blank=True,
        related_name="collections",
        through="CollectionProduct",
        through_fields=("collection", "product"),
    )
    background_image = VersatileImageField(
        upload_to=UploadToPathAndRename(path="collection-backgrounds", field="name"),
        blank=True,
        null=True,
    )
    background_image_alt = models.CharField(max_length=128, blank=True)
    description = JSONField(blank=True, default=dict)

    class Meta:
        ordering = ("slug",)
        permissions = ((CollectionPermissions.MANAGE_COLLECTIONS.codename, "Manage collections"),)

    def __str__(self):
        return self.name


class CollectionProduct(SortableModel):
    collection = models.ForeignKey(
        "Collection", related_name="collectionproduct", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "products.Product", related_name="collectionproduct", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("collection", "product"),)

    def get_ordering_queryset(self):
        return self.product.collectionproduct.all()
