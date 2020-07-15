import graphene

from core.decorators import permission_required
from core.graph.fields import BaseDjangoConnectionField
from .filters import PluginFilterInput
from .mutations import PluginUpdate
from .resolvers import resolve_plugin, resolve_plugins
from .types import Plugin
from ..core.permissions import PluginsPermissions


class PluginsQueries(graphene.ObjectType):
    plugin = graphene.Field(
        Plugin,
        id=graphene.Argument(graphene.ID, description="ID of the plugin.", required=True),
        description="Look up a plugin by ID.",
    )
    plugins = BaseDjangoConnectionField(
        Plugin,
        filter=PluginFilterInput(description="Filtering options for plugins."),
        description="List of plugins.",
    )

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    def resolve_plugin(self, _info, **data):
        return resolve_plugin(data.get("id"))

    @permission_required(PluginsPermissions.MANAGE_PLUGINS)
    def resolve_plugins(self, _info, **kwargs):
        return resolve_plugins(**kwargs)


class PluginsMutations(graphene.ObjectType):
    plugin_update = PluginUpdate.Field()
