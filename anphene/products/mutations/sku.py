import graphene

from core.graph.mutations import BaseMutation
from .. import models
from ..types.products import Product
from ...core.permissions import ProductPermissions


class GenerateSKU(BaseMutation):
    sku = graphene.String(description="Unique SKU generate by system.")

    class Arguments:
        product_id = graphene.Argument(graphene.ID, description="Product id.", required=False)
        name = graphene.String(description="Product name for single sku.", required=False)

    class Meta:
        description = "Generator for sku system on anphene."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        product_id = data.get("product_id", None)
        name = data.get("name", None)

        sku = ""
        if product_id:
            product = cls.get_node_or_error(info, product_id, field="id", only_type=Product)
            sku = product.name[0:3].upper()
        if name:
            sku = name[0:3].upper()

        unique_sku = sku
        sku_checker = models.ProductVariant.objects.filter(sku__istartswith=unique_sku).exists()

        extension = 0
        while sku_checker:
            extension += 1
            unique_sku = f"{sku}{extension}"
            sku_checker = models.ProductVariant.objects.filter(
                sku__istartswith=unique_sku
            ).exists()

        return GenerateSKU(sku=unique_sku)
