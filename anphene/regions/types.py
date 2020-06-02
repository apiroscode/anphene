from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import PrefetchingConnectionField
from . import models
from .dataloader import (
    CityByProvinceIdLoader,
    SubDistrictByCityIdLoader,
)


class SubDistrict(CountableDjangoObjectType):
    class Meta:
        description = "Sub District"
        interfaces = [relay.Node]
        model = models.SubDistrict


class City(CountableDjangoObjectType):
    class Meta:
        description = "City"
        interfaces = [relay.Node]
        model = models.City

    @staticmethod
    def resolve_name(root, _info):
        return root.city_name

    @staticmethod
    def resolve_sub_districts(root: models.City, info, **kwargs):
        return SubDistrictByCityIdLoader(info.context).load(root.id)


class Province(CountableDjangoObjectType):
    cities = PrefetchingConnectionField(City)

    class Meta:
        description = "Province"
        interfaces = [relay.Node]
        model = models.Province

    @staticmethod
    def resolve_cities(root: models.Province, info, **kwargs):
        return CityByProvinceIdLoader(info.context).load(root.id)
