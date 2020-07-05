import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from . import models
from ..core.permissions import AttributePermissions


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of attribute IDs to delete."
        )

    class Meta:
        description = "Deletes attributes."
        model = models.Attribute
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)
