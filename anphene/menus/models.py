from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from core.db.models import SortableModel
from ..categories.models import Category
from ..collections.models import Collection
from ..core.permissions import MenuPermissions
from ..pages.models import Page


class Menu(models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        ordering = ("pk",)
        permissions = ((MenuPermissions.MANAGE_MENUS.codename, "Manage navigation."),)

    def __str__(self):
        return self.name


class MenuItem(MPTTModel, SortableModel):
    menu = models.ForeignKey(Menu, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    # not mandatory fields, usage depends on what type of link is stored
    url = models.URLField(max_length=256, blank=True, null=True)
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, blank=True, null=True, on_delete=models.CASCADE)
    page = models.ForeignKey(Page, blank=True, null=True, on_delete=models.CASCADE)

    objects = models.Manager()
    tree = TreeManager()

    class Meta:
        ordering = ("sort_order",)

    def __str__(self):
        return f"{self.name}-{self.id}"

    def get_ordering_queryset(self):
        return self.menu.items.all() if not self.parent else self.parent.children.all()

    @property
    def linked_object(self):
        return self.category or self.collection or self.page

    def is_public(self):
        return not self.linked_object or getattr(self.linked_object, "is_published", True)
