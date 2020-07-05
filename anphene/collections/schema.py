import graphene

from core.graph.fields import FilterInputConnectionField
from core.graph.utils import get_node_or_slug
from .filters import CollectionFilterInput
from .mutations import (
    CollectionCreate,
    CollectionDelete,
    CollectionUpdate,
    AssignCollectionHomepage,
)
from .mutations_bulk import (
    CollectionAddProducts,
    CollectionBulkDelete,
    CollectionBulkPublish,
    CollectionRemoveProducts,
)
from .resolvers import resolve_collections
from .sorters import CollectionSortingInput
from .types import Collection


class CollectionQueries(graphene.ObjectType):
    collection = graphene.Field(
        Collection,
        id=graphene.Argument(graphene.ID, description="ID of the collection.", required=True),
        description="Look up a collection by ID.",
    )
    collections = FilterInputConnectionField(
        Collection,
        filter=CollectionFilterInput(description="Filtering options for collections."),
        sort_by=CollectionSortingInput(description="Sort collections."),
        description="List of the shop's collections.",
    )

    def resolve_collection(self, info, id):
        return get_node_or_slug(info, id, Collection)

    def resolve_collections(self, info, **kwargs):
        return resolve_collections(info, **kwargs)


class CollectionMutations(graphene.ObjectType):
    collection_create = CollectionCreate.Field()
    collection_update = CollectionUpdate.Field()
    collection_delete = CollectionDelete.Field()
    collection_bulk_delete = CollectionBulkDelete.Field()
    collection_bulk_publish = CollectionBulkPublish.Field()
    collection_add_products = CollectionAddProducts.Field()
    collection_remove_products = CollectionRemoveProducts.Field()
    assign_collection_homepage = AssignCollectionHomepage.Field()
