from typing import Any, List, Optional, TYPE_CHECKING

from django.conf import settings
from django.utils.module_loading import import_string

from . import PluginType
from .models import PluginConfiguration
from .tools import get_updated_configuration
from ..shipping import Waybill

if TYPE_CHECKING:
    from .base_plugin import BasePlugin
    from ..users.models import Address
    from ..shipping import Courier


class PluginsManager(object):
    """Base manager for handling plugins logic."""

    plugins: List["BasePlugin"] = []

    def __init__(self, plugins: List[str]):
        self.plugins = []
        all_configs = self._get_all_plugin_configs()
        for plugin_path in plugins:
            PluginClass = import_string(plugin_path)
            if PluginClass.PLUGIN_ID in all_configs:
                existing_config = all_configs[PluginClass.PLUGIN_ID]
                plugin_config = existing_config.configuration
                active = existing_config.active
            else:
                plugin_config = PluginClass.DEFAULT_CONFIGURATION
                active = PluginClass.get_default_active()
            self.plugins.append(PluginClass(configuration=plugin_config, active=active))

    def __run_method_on_plugins(self, method_name: str, default_value: Any, *args, **kwargs):
        """Try to run a method with the given name on each declared plugin."""
        value = default_value
        for plugin in self.plugins:
            if plugin.active:
                value = self.__run_method_on_single_plugin(
                    plugin, method_name, value, *args, **kwargs
                )
        return value

    def __run_method_on_single_plugin(
        self,
        plugin: Optional["BasePlugin"],
        method_name: str,
        previous_value: Any,
        *args,
        **kwargs,
    ) -> Any:
        """Run method_name on plugin.

        Method will return value returned from plugin's
        method. If plugin doesn't have own implementation of expected method_name, it
        will return previous_value.
        """
        plugin_method = getattr(plugin, method_name, NotImplemented)
        if plugin_method == NotImplemented:
            return previous_value

        returned_value = plugin_method(*args, **kwargs, previous_value=previous_value)
        if returned_value == NotImplemented:
            return previous_value
        return returned_value

    def _get_all_plugin_configs(self):
        if not hasattr(self, "_plugin_configs"):
            self._plugin_configs = {pc.identifier: pc for pc in PluginConfiguration.objects.all()}
        return self._plugin_configs

    def save_plugin_configuration(self, plugin_id, cleaned_data: dict):
        for plugin in self.plugins:
            if plugin.PLUGIN_ID == plugin_id:
                plugin_configuration, _ = PluginConfiguration.objects.get_or_create(
                    identifier=plugin_id,
                    defaults={
                        "active": plugin.DEFAULT_ACTIVE,
                        "configuration": plugin.configuration,
                    },
                )

                # set All fetch_shipping_cost and fetch_waybill to false first
                if plugin.PLUGIN_TYPE == PluginType.SHIPPING:
                    self.set_shipping_plugins(plugin_id, cleaned_data)

                return plugin.save_plugin_configuration(plugin_configuration, cleaned_data)

    def get_plugin(self, plugin_id: str) -> Optional["BasePlugin"]:
        for plugin in self.plugins:
            if plugin.PLUGIN_ID == plugin_id:
                return plugin
        return None

    def list_shipping_plugins(self) -> List["BasePlugin"]:
        plugins = self.plugins
        return [plugin for plugin in plugins if plugin.PLUGIN_TYPE == PluginType.SHIPPING]

    def set_shipping_plugins(self, plugin_id, cleaned_data):
        fields = ["fetch_shipping_cost", "fetch_waybill"]
        configuration = cleaned_data.get("configuration", [])
        updated_configuration = get_updated_configuration(configuration, fields)
        plugins = [
            plugin for plugin in self.list_shipping_plugins() if plugin.PLUGIN_ID != plugin_id
        ]

        if updated_configuration:
            for plugin in plugins:
                plugin_configuration, _ = PluginConfiguration.objects.get_or_create(
                    identifier=plugin.PLUGIN_ID,
                    defaults={
                        "active": plugin.DEFAULT_ACTIVE,
                        "configuration": plugin.configuration,
                    },
                )
                plugin.save_plugin_configuration(
                    plugin_configuration, {"configuration": updated_configuration}
                )

    def fetch_shipping_cost(self, address: "Address", weight: int) -> List["Courier"]:
        default_value = []
        return self.__run_method_on_plugins("fetch_shipping_costs", default_value, address, weight)

    def fetch_waybill(self, waybill: str, courier: str) -> Optional["Waybill"]:
        default_value = None
        return self.__run_method_on_plugins("fetch_waybill", default_value, waybill, courier)


def get_plugins_manager(manager_path: str = None, plugins: List[str] = None) -> PluginsManager:
    if not manager_path:
        manager_path = settings.PLUGINS_MANAGER
    if plugins is None:
        plugins = settings.PLUGINS
    manager = import_string(manager_path)
    return manager(plugins)
