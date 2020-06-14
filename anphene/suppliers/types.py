from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from . import models


class Supplier(CountableDjangoObjectType):
    class Meta:
        description = (
            "Represents a type of suppliers. Suppliers are needed to facilitate stock "
            "management in the warehouse"
        )
        interfaces = [relay.Node]
        model = models.Supplier
