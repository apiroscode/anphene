import graphene

from core.graph.mutations import ModelBulkDeleteMutation
from . import models
from ..core.permissions import MenuPermissions


class MenuBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of menu IDs to delete.")

    class Meta:
        description = "Deletes menus."
        model = models.Menu
        permissions = (MenuPermissions.MANAGE_MENUS,)


class MenuItemBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of menu item IDs to delete."
        )

    class Meta:
        description = "Deletes menu items."
        model = models.MenuItem
        permissions = (MenuPermissions.MANAGE_MENUS,)
