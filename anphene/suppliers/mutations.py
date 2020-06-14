import graphene
from ..core.permissions import SupplierPermissions
from core.graph.mutations import ModelMutation, ModelBulkDeleteMutation, ModelDeleteMutation
from . import models


class SupplierInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the supplier")
    email = graphene.String(description="Email of the supplier")
    phone = graphene.String(description="Phone of the supplier")
    address = graphene.String(description="Address of the supplier")


class SupplierCreate(ModelMutation):
    class Arguments:
        input = SupplierInput(required=True, description="Fields required to create a supplier")

    class Meta:
        description = "Creates a new supplier."
        model = models.Supplier
        permissions = (SupplierPermissions.MANAGE_SUPPLIERS,)


class SupplierUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a supplier to update.")
        input = SupplierInput(required=True, description="Fields required to create a supplier")

    class Meta:
        description = "Updates an existing supplier."
        model = models.Supplier
        permissions = (SupplierPermissions.MANAGE_SUPPLIERS,)


class SupplierDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a supplier to update.")

    class Meta:
        description = "Deletes a supplier."
        model = models.Supplier
        permissions = (SupplierPermissions.MANAGE_SUPPLIERS,)


class SupplierBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of supplier IDs to delete."
        )

    class Meta:
        description = "Deletes a suppliers."
        model = models.Supplier
        permissions = (SupplierPermissions.MANAGE_SUPPLIERS,)
