from graphene import relay
from . import models
from core.graph.connection import CountableDjangoObjectType


class Page(CountableDjangoObjectType):
    class Meta:
        description = (
            "A static page that can be manually added by a shop operator through the dashboard."
        )
        interfaces = [relay.Node]
        model = models.Page
