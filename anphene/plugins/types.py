from typing import Optional, TYPE_CHECKING

import graphene

from core.graph.connection import CountableDjangoObjectType
from . import manager, models
from .base_plugin import ConfigurationTypeField
from .enums import ConfigurationTypeFieldEnum

if TYPE_CHECKING:
    # flake8: noqa
    from .base_plugin import PluginConfigurationType


class ConfigurationItem(graphene.ObjectType):
    name = graphene.String(required=True, description="Name of the field.")
    value = graphene.String(required=False, description="Current value of the field.")
    type = graphene.Field(ConfigurationTypeFieldEnum, description="Type of the field.")
    help_text = graphene.String(required=False, description="Help text for the field.")
    label = graphene.String(required=False, description="Label for the field.")

    class Meta:
        description = "Stores information about a single configuration field."


class Plugin(CountableDjangoObjectType):
    id = graphene.Field(type=graphene.ID, required=True)
    configuration = graphene.List(ConfigurationItem)

    class Meta:
        description = "Plugin."
        model = models.PluginConfiguration
        interfaces = [graphene.relay.Node]
        only_fields = ["id", "name", "description", "active", "configuration", "type"]

    def resolve_id(self: models.PluginConfiguration, _info):
        return self.id

    @staticmethod
    def resolve_configuration(
        root: models.PluginConfiguration, _info
    ) -> Optional["PluginConfigurationType"]:
        plugin = manager.get_plugins_manager().get_plugin(str(root.id))
        if not plugin:
            return None
        configuration = plugin.configuration

        return configuration
