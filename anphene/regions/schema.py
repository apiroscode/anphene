import graphene

from core.graph.fields import BaseDjangoConnectionField, FilterInputConnectionField
from core.graph.types import FilterInputObjectType
from .filters import CityFilter, SubDistrictFilter
from .types import City, Province, SubDistrict
import graphene_django_optimizer as gql_optimizer
from . import models


class CityFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CityFilter


class SubDistrictFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SubDistrictFilter


class RegionQueries(graphene.ObjectType):
    provinces = BaseDjangoConnectionField(Province, description="List of provinces")
    cities = FilterInputConnectionField(
        City,
        filter=CityFilterInput(description="Filtering options for customers."),
        description="List of city.",
    )

    sub_districts = FilterInputConnectionField(
        SubDistrict,
        filter=SubDistrictFilterInput(description="Filtering options for customers."),
        description="List of districts.",
    )
