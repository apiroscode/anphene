import graphene

from ..regions.schema import RegionQueries
from ..users.schema import UserMutations, UserQueries


class Query(RegionQueries, UserQueries):
    pass


class Mutation(UserMutations):
    pass


schema = graphene.Schema(query=Query, mutation=UserMutations)
