import graphene

from ..attributes.schema import AttributeQueries, AttributeMutations
from ..regions.schema import RegionQueries
from ..users.schema import UserMutations, UserQueries


class Query(AttributeQueries, RegionQueries, UserQueries):
    pass


class Mutation(AttributeMutations, UserMutations):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
