import graphene

from core.graph.fields import FilterInputConnectionField
from .filters import SupplierFilterInput
from .mutations import SupplierCreate, SupplierDelete, SupplierUpdate
from .mutations_bulk import SupplierBulkDelete
from .resolvers import resolve_suppliers
from .sorters import SupplierSortingInput
from .types import Supplier


class SupplierQueries(graphene.ObjectType):
    supplier = graphene.Field(
        Supplier,
        id=graphene.Argument(graphene.ID, description="ID of the supplier.", required=True),
        description="Look up a supplier by ID.",
    )
    suppliers = FilterInputConnectionField(
        Supplier,
        filter=SupplierFilterInput(description="Filtering options for suppliers."),
        sort_by=SupplierSortingInput(description="Sort product suppliers."),
        description="List of the suppliers.",
    )

    def resolve_supplier(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Supplier)

    def resolve_suppliers(self, info, **kwargs):
        return resolve_suppliers(info, **kwargs)


class SupplierMutations(graphene.ObjectType):
    supplier_create = SupplierCreate.Field()
    supplier_update = SupplierUpdate.Field()
    supplier_delete = SupplierDelete.Field()
    supplier_bulk_delete = SupplierBulkDelete.Field()
