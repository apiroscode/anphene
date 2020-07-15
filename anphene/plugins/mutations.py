import graphene
from django.core.exceptions import ValidationError

from core.graph.mutations import BaseMutation
from .manager import get_plugins_manager
from .types import Plugin
from ..core.permissions import PluginsPermissions


class ConfigurationItemInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the field to update.")
    value = graphene.String(required=False, description="Value of the given field to update.")


class PluginUpdateInput(graphene.InputObjectType):
    active = graphene.Boolean(
        required=False, description="Indicates whether the plugin should be enabled."
    )
    configuration = graphene.List(
        ConfigurationItemInput, required=False, description="Configuration of the plugin.",
    )


class PluginUpdate(BaseMutation):
    plugin = graphene.Field(Plugin)

    class Arguments:
        id = graphene.ID(required=True, description="ID of plugin to update.")
        input = PluginUpdateInput(
            description="Fields required to update a plugin configuration.", required=True,
        )

    class Meta:
        description = "Update plugin configuration."
        permissions = (PluginsPermissions.MANAGE_PLUGINS,)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        plugin_id = data.get("id")
        data = data.get("input")
        manager = get_plugins_manager()
        plugin = manager.get_plugin(plugin_id)
        if not plugin:
            raise ValidationError({"id": ValidationError("Plugin doesn't exist")})
        instance = manager.save_plugin_configuration(plugin_id, data)
        return PluginUpdate(plugin=instance)
