import graphene


class PluginFilterInput(graphene.InputObjectType):
    active = graphene.Argument(graphene.Boolean)
