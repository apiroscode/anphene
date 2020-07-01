import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from . import models
from ..core.permissions import SupplierPermissions


class SupplierBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of supplier IDs to delete."
        )

    class Meta:
        description = "Deletes a suppliers."
        model = models.Supplier
        permissions = (SupplierPermissions.MANAGE_SUPPLIERS,)
