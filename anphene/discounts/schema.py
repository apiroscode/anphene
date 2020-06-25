import graphene

from core.decorators import permission_required
from core.graph.fields import FilterInputConnectionField
from .filters import SaleFilterInput, VoucherFilterInput
from .mutations import (
    SaleAddCatalogues,
    SaleBulkDelete,
    SaleCreate,
    SaleDelete,
    SaleRemoveCatalogues,
    SaleUpdate,
    VoucherAddCatalogues,
    VoucherBulkDelete,
    VoucherCreate,
    VoucherDelete,
    VoucherRemoveCatalogues,
    VoucherUpdate,
)
from .resolvers import resolve_sales, resolve_vouchers
from .sorters import SaleSortingInput, VoucherSortingInput
from .types import Sale, Voucher
from ..core.permissions import DiscountPermissions


class DiscountQueries(graphene.ObjectType):
    sale = graphene.Field(
        Sale,
        id=graphene.Argument(graphene.ID, description="ID of the sale.", required=True),
        description="Look up a sale by ID.",
    )
    sales = FilterInputConnectionField(
        Sale,
        filter=SaleFilterInput(description="Filtering options for sales."),
        sort_by=SaleSortingInput(description="Sort sales."),
        description="List of the shop's sales.",
    )
    voucher = graphene.Field(
        Voucher,
        id=graphene.Argument(graphene.ID, description="ID of the voucher.", required=True),
        description="Look up a voucher by ID.",
    )
    vouchers = FilterInputConnectionField(
        Voucher,
        filter=VoucherFilterInput(description="Filtering options for vouchers."),
        sort_by=VoucherSortingInput(description="Sort voucher."),
        description="List of the shop's vouchers.",
    )

    @permission_required(DiscountPermissions.MANAGE_DISCOUNTS)
    def resolve_sale(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Sale)

    @permission_required(DiscountPermissions.MANAGE_DISCOUNTS)
    def resolve_sales(self, info, **kwargs):
        return resolve_sales(info, **kwargs)

    @permission_required(DiscountPermissions.MANAGE_DISCOUNTS)
    def resolve_voucher(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Voucher)

    @permission_required(DiscountPermissions.MANAGE_DISCOUNTS)
    def resolve_vouchers(self, info, **kwargs):
        return resolve_vouchers(info, **kwargs)


class DiscountMutations(graphene.ObjectType):
    sale_create = SaleCreate.Field()
    sale_update = SaleUpdate.Field()
    sale_delete = SaleDelete.Field()
    sale_bulk_delete = SaleBulkDelete.Field()
    sale_catalogues_add = SaleAddCatalogues.Field()
    sale_catalogues_remove = SaleRemoveCatalogues.Field()

    voucher_create = VoucherCreate.Field()
    voucher_update = VoucherUpdate.Field()
    voucher_delete = VoucherDelete.Field()
    voucher_bulk_delete = VoucherBulkDelete.Field()
    voucher_catalogues_add = VoucherAddCatalogues.Field()
    voucher_catalogues_remove = VoucherRemoveCatalogues.Field()
