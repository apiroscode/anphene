import graphene

from core.graph.fields import FilterInputConnectionField
from .filters import AttributeFilterInput
from .mutations import (
    AttributeBulkDelete,
    AttributeCreate,
    AttributeDelete,
    AttributeReorderValues,
    AttributeUpdate,
    AttributeValueCreate,
    AttributeValueDelete,
    AttributeValueUpdate,
)
from .resolvers import resolve_attributes
from .sorters import AttributeSortingInput
from .types import Attribute


class AttributeQueries(graphene.ObjectType):
    attribute = graphene.Field(
        Attribute,
        id=graphene.Argument(graphene.ID, description="ID of the attribute.", required=True),
        description="Look up an attribute by ID.",
    )
    attributes = FilterInputConnectionField(
        Attribute,
        description="List of the shop's attributes.",
        filter=AttributeFilterInput(description="Filtering options for attributes."),
        sort_by=AttributeSortingInput(description="Sorting options for attributes."),
    )

    def resolve_attributes(self, info, **kwargs):
        return resolve_attributes(info, **kwargs)

    def resolve_attribute(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Attribute)


class AttributeMutations(graphene.ObjectType):
    attribute_create = AttributeCreate.Field()
    attribute_update = AttributeUpdate.Field()
    attribute_delete = AttributeDelete.Field()
    attribute_bulk_delete = AttributeBulkDelete.Field()

    attribute_value_create = AttributeValueCreate.Field()
    attribute_value_update = AttributeValueUpdate.Field()
    attribute_value_delete = AttributeValueDelete.Field()
    attribute_reorder_values = AttributeReorderValues.Field()
