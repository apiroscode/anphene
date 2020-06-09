import graphene

from ..attributes.schema import AttributeMutations, AttributeQueries
from ..products.schema import ProductMutations, ProductQueries
from ..regions.schema import RegionQueries
from ..users.schema import UserMutations, UserQueries


class Query(AttributeQueries, ProductQueries, RegionQueries, UserQueries):
    pass


class Mutation(AttributeMutations, ProductMutations, UserMutations):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
