from copy import copy
from typing import TYPE_CHECKING, Any, List, Optional, Union

from .models import PluginConfiguration

if TYPE_CHECKING:
    from ..users.models import Address
    from ..shipping import Courier, Waybill

PluginConfigurationType = List[dict]


class ConfigurationTypeField:
    STRING = "String"
    BOOLEAN = "Boolean"
    INTEGER = "Integer"
    CHOICES = [
        (STRING, "Field is a String"),
        (BOOLEAN, "Field is a Boolean"),
        (INTEGER, "Field is a Integer"),
    ]


class BasePlugin:
    """Abstract class for storing all methods available for any plugin.

    All methods take previous_value parameter.
    previous_value contains a value calculated by the previous plugin in the queue.
    If the plugin is first, it will use default value calculated by the manager.
    """

    PLUGIN_ID = ""
    PLUGIN_NAME = ""
    PLUGIN_DESCRIPTION = ""
    PLUGIN_TYPE = ""
    CONFIG_STRUCTURE = None
    DEFAULT_CONFIGURATION = []
    DEFAULT_ACTIVE = False

    def __init__(self, *, configuration: PluginConfigurationType, active: bool):
        self.configuration = self.get_plugin_configuration(configuration)
        self.active = active

    def __str__(self):
        return self.PLUGIN_NAME

    @classmethod
    def get_default_active(cls):
        return cls.DEFAULT_ACTIVE

    def get_plugin_configuration(
        self, configuration: PluginConfigurationType
    ) -> PluginConfigurationType:
        if not configuration:
            configuration = []
        self._update_configuration_structure(configuration)
        if configuration:
            # Let's add a translated descriptions and labels
            self._append_config_structure(configuration)
        return configuration

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct.

        Raise django.core.exceptions.ValidationError otherwise.
        """
        return

    @classmethod
    def save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration", cleaned_data):
        current_config = plugin_configuration.configuration
        configuration_to_update = cleaned_data.get("configuration")
        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)
        if "active" in cleaned_data:
            plugin_configuration.active = cleaned_data["active"]
        cls.validate_plugin_configuration(plugin_configuration)
        plugin_configuration.save()
        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)
        # change id to identifier
        plugin_configuration.id = cls.PLUGIN_ID
        plugin_configuration.name = cls.PLUGIN_NAME
        plugin_configuration.description = cls.PLUGIN_DESCRIPTION
        return plugin_configuration

    @classmethod
    def _append_config_structure(cls, configuration: PluginConfigurationType):
        """Append configuration structure to config from the database.

        Database stores "key: value" pairs, the definition of fields should be declared
        inside of the plugin. Based on this, the plugin will generate a structure of
        configuration with current values and provide access to it via API.
        """
        config_structure = getattr(cls, "CONFIG_STRUCTURE", {})
        for configuration_field in configuration:

            structure_to_add = config_structure.get(configuration_field.get("name"))
            if structure_to_add:
                configuration_field.update(structure_to_add)

    @classmethod
    def _update_configuration_structure(cls, configuration: PluginConfigurationType):
        config_structure = getattr(cls, "CONFIG_STRUCTURE", {})
        desired_config_keys = set(config_structure.keys())

        configured_keys = set(d["name"] for d in configuration)
        missing_keys = desired_config_keys - configured_keys

        if not missing_keys:
            return

        default_config = cls.DEFAULT_CONFIGURATION
        if not default_config:
            return

        update_values = [copy(k) for k in default_config if k["name"] in missing_keys]
        configuration.extend(update_values)

    @classmethod
    def _update_config_items(cls, configuration_to_update: List[dict], current_config: List[dict]):
        config_structure: dict = (cls.CONFIG_STRUCTURE if cls.CONFIG_STRUCTURE is not None else {})
        for config_item in current_config:
            for config_item_to_update in configuration_to_update:
                config_item_name = config_item_to_update.get("name")
                if config_item["name"] == config_item_name:
                    new_value = config_item_to_update.get("value")
                    item_type = config_structure.get(config_item_name, {}).get("type")
                    if (
                        item_type == ConfigurationTypeField.BOOLEAN
                        and new_value
                        and not isinstance(new_value, bool)
                    ):
                        new_value = new_value.lower() == "true"
                    config_item.update([("value", new_value)])

        # Get new keys that don't exist in current_config and extend it.
        current_config_keys = set(c_field["name"] for c_field in current_config)
        configuration_to_update_dict = {
            c_field["name"]: c_field["value"] for c_field in configuration_to_update
        }
        missing_keys = set(configuration_to_update_dict.keys()) - current_config_keys
        for missing_key in missing_keys:
            if not config_structure.get(missing_key):
                continue
            current_config.append(
                {"name": missing_key, "value": configuration_to_update_dict[missing_key],}
            )

    def fetch_shipping_costs(
        self, address: "Address", weight: int, previous_value: list
    ) -> List["Courier"]:
        return NotImplemented

    def fetch_waybill(
        self, waybill: str, courier: str, previous_value: "Waybill"
    ) -> Optional["Waybill"]:
        return NotImplemented
