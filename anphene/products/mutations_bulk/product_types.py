import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from ...core.permissions import ProductPermissions
from ...products import models


class ProductTypeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product type IDs to delete."
        )

    class Meta:
        description = "Deletes product types."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCT_TYPES,)
