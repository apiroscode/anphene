import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from .. import models
from ..utils import CustomerDeleteMixin
from ...core.permissions import UserPermissions


class CustomerBulkDelete(CustomerDeleteMixin, ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of user IDs to delete.")

    class Meta:
        description = "Deletes customers."
        model = models.User
        permissions = (UserPermissions.MANAGE_CUSTOMERS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        count, errors = super().perform_mutation(root, info, **data)
        cls.post_process(info, count)
        return count, errors
