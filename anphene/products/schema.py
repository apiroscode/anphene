import graphene

from core.graph.fields import FilterInputConnectionField
from .filters import ProductTypeFilterInput
from .mutations.product_types import (
    AttributeAssign,
    AttributeUnassign,
    ProductTypeBulkDelete,
    ProductTypeCreate,
    ProductTypeDelete,
    ProductTypeReorderAttributes,
    ProductTypeUpdate,
)
from .resolvers import resolve_product_types
from .sorters import ProductTypeSortingInput
from .types.product_types import ProductType


class ProductQueries(graphene.ObjectType):
    product_type = graphene.Field(
        ProductType,
        id=graphene.Argument(graphene.ID, description="ID of the product type.", required=True),
        description="Look up a product type by ID.",
    )
    product_types = FilterInputConnectionField(
        ProductType,
        filter=ProductTypeFilterInput(description="Filtering options for product types."),
        sort_by=ProductTypeSortingInput(description="Sort product types."),
        description="List of the shop's product types.",
    )

    def resolve_product_type(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductType)

    def resolve_product_types(self, info, **kwargs):
        return resolve_product_types(info, **kwargs)


class ProductMutations(graphene.ObjectType):
    # Product Types mutations
    product_type_create = ProductTypeCreate.Field()
    product_type_update = ProductTypeUpdate.Field()
    product_type_delete = ProductTypeDelete.Field()
    product_type_bulk_delete = ProductTypeBulkDelete.Field()
    product_type_reorder_attribute = ProductTypeReorderAttributes.Field()
    attribute_assign = AttributeAssign.Field()
    attribute_unassign = AttributeUnassign.Field()
