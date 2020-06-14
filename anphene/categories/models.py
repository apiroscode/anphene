from django.contrib.postgres.fields import JSONField
from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from versatileimagefield.fields import VersatileImageField

from core.db.models import SeoModel
from core.utils.images import UploadToPathAndRename
from ..core.permissions import CategoryPermissions


class Category(MPTTModel, SeoModel):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    description = JSONField(blank=True, default=dict)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    background_image = VersatileImageField(
        upload_to=UploadToPathAndRename(path="category-backgrounds", field="name"),
        blank=True,
        null=True,
    )
    background_image_alt = models.CharField(max_length=128, blank=True)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        permissions = ((CategoryPermissions.MANAGE_CATEGORIES.codename, "Manage categories"),)

    def __str__(self):
        return self.name
