import graphene

from ..attributes.schema import AttributeMutations, AttributeQueries
from ..categories.schema import CategoryMutations, CategoryQueries
from ..collections.schema import CollectionMutations, CollectionQueries
from ..products.schema import ProductMutations, ProductQueries
from ..regions.schema import RegionQueries
from ..suppliers.schema import SupplierMutations, SupplierQueries
from ..users.schema import UserMutations, UserQueries


class Query(
    AttributeQueries,
    CategoryQueries,
    CollectionQueries,
    ProductQueries,
    RegionQueries,
    SupplierQueries,
    UserQueries,
):
    pass


class Mutation(
    AttributeMutations,
    CategoryMutations,
    CollectionMutations,
    ProductMutations,
    SupplierMutations,
    UserMutations,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
