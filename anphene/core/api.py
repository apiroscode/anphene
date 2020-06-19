import graphene

from ..attributes.schema import AttributeMutations, AttributeQueries
from ..categories.schema import CategoryMutations, CategoryQueries
from ..collections.schema import CollectionMutations, CollectionQueries
from ..discounts.schema import DiscountMutations, DiscountQueries
from ..products.schema import ProductMutations, ProductQueries
from ..regions.schema import RegionQueries
from ..suppliers.schema import SupplierMutations, SupplierQueries
from ..users.schema import UserMutations, UserQueries


class Query(
    AttributeQueries,
    CategoryQueries,
    CollectionQueries,
    DiscountQueries,
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
    DiscountMutations,
    ProductMutations,
    SupplierMutations,
    UserMutations,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
