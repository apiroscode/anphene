from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = "anphene.plugins"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import types

        # noinspection PyUnresolvedReferences
        from .checks import check_plugins
