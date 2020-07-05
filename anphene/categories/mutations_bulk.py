import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from . import models
from .utils import delete_categories
from ..core.permissions import CategoryPermissions


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of category IDs to delete."
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        permissions = (CategoryPermissions.MANAGE_CATEGORIES,)

    @classmethod
    def bulk_action(cls, queryset):
        delete_categories(queryset.values_list("pk", flat=True))
