from django.apps import AppConfig


class MenusConfig(AppConfig):
    name = "anphene.menus"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import types
