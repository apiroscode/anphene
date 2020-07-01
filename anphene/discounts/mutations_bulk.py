import graphene

from core.graph.mutations import (
    BaseMutation,
    ModelBulkDeleteMutation,
)
from . import models
from .types import Sale, Voucher
from ..categories.types import Category
from ..collections.types import Collection
from ..core.permissions import DiscountPermissions
from ..products.types.products import Product


class CatalogueInput(graphene.InputObjectType):
    products = graphene.List(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = graphene.List(
        graphene.ID, description="Categories related to the discount.", name="categories",
    )
    collections = graphene.List(
        graphene.ID, description="Collections related to the discount.", name="collections",
    )


class BaseDiscountCatalogueMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def add_catalogues_to_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            node.products.add(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.add(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.add(*collections)

    @classmethod
    def remove_catalogues_from_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            node.products.remove(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.remove(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.remove(*collections)


class VoucherBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            required=True, description="Fields required to modify catalogue IDs of voucher.",
        )

    class Meta:
        abstract = True


class VoucherAddCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        cls.add_catalogues_to_node(voucher, data.get("input"))
        return VoucherAddCatalogues(voucher=voucher)


class VoucherRemoveCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        voucher = cls.get_node_or_error(
            info, data.get("id"), only_type=Voucher, field="voucher_id"
        )
        cls.remove_catalogues_from_node(voucher, data.get("input"))
        return VoucherRemoveCatalogues(voucher=voucher)


class VoucherBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of voucher IDs to delete."
        )

    class Meta:
        description = "Deletes vouchers."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class SaleBaseCatalogueMutation(BaseDiscountCatalogueMutation):
    sale = graphene.Field(Sale, description="Sale of which catalogue IDs will be modified.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale.")
        input = CatalogueInput(
            required=True, description="Fields required to modify catalogue IDs of sale.",
        )

    class Meta:
        abstract = True


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(info, data.get("id"), only_type=Sale, field="sale_id")
        cls.add_catalogues_to_node(sale, data.get("input"))
        return SaleAddCatalogues(sale=sale)


class SaleRemoveCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = "Removes products, categories, collections from a sale."
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        sale = cls.get_node_or_error(info, data.get("id"), only_type=Sale, field="sale_id")
        cls.remove_catalogues_from_node(sale, data.get("input"))
        return SaleRemoveCatalogues(sale=sale)


class SaleBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of sale IDs to delete.")

    class Meta:
        description = "Deletes sales."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
