import graphene

from core.graph.mutations import BaseMutation
from ..utils.sku import generate_sku
from ...core.permissions import ProductPermissions


class GenerateSKU(BaseMutation):
    sku = graphene.String(description="Unique SKU generate by system.")

    class Arguments:
        name = graphene.String(description="Product name for single sku.", required=False)

    class Meta:
        description = "Generator for sku system on anphene."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        name = data.get("name", None)
        return GenerateSKU(sku=generate_sku(name))
