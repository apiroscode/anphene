import graphene

from core.graph.mutations import (
    BaseBulkMutation,
    ModelBulkDeleteMutation,
)
from .. import models
from ...core.permissions import UserPermissions


class StaffBulkActivate(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of staff IDs to delete.")
        is_active = graphene.Boolean(
            required=True, description="Determine if staff will be active or not.",
        )

    class Meta:
        description = "Activate staff."
        model = models.User
        permissions = (UserPermissions.MANAGE_STAFF,)

    @classmethod
    def bulk_action(cls, queryset, is_active):
        queryset.update(is_active=is_active)


class StaffBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of staff IDs to delete.")

    class Meta:
        description = "Deletes staff."
        model = models.User
        permissions = (UserPermissions.MANAGE_STAFF,)
