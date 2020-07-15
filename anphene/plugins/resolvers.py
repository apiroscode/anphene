from .base_plugin import BasePlugin
from .manager import get_plugins_manager
from .models import PluginConfiguration


def resolve_plugin(plugin_id):
    manager = get_plugins_manager()
    plugin: BasePlugin = manager.get_plugin(plugin_id)
    if not plugin:
        return None
    return PluginConfiguration(
        id=plugin.PLUGIN_ID,
        active=plugin.active,
        configuration=plugin.configuration,
        description=plugin.PLUGIN_DESCRIPTION,
        name=plugin.PLUGIN_NAME,
    )


def resolve_plugins(**kwargs):
    plugin_filter = kwargs.get("filter", {})
    filter_active = plugin_filter.get("active")

    manager = get_plugins_manager()
    plugins = manager.plugins

    if filter_active is not None:
        plugins = [plugin for plugin in plugins if plugin.active is filter_active]

    return [
        PluginConfiguration(
            id=plugin.PLUGIN_ID,
            active=plugin.active,
            configuration=plugin.configuration,
            description=plugin.PLUGIN_DESCRIPTION,
            name=plugin.PLUGIN_NAME,
            type=plugin.PLUGIN_TYPE,
        )
        for plugin in plugins
    ]
