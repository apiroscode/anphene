import graphene
from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from core.graph.types import Image
from .. import models


class Product(CountableDjangoObjectType):
    class Meta:
        description = "Represents a collection of products."

        interfaces = [relay.Node]
        model = models.Product
