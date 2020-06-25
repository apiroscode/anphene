from django.apps import AppConfig


class PagesConfig(AppConfig):
    name = "anphene.pages"

    def ready(self):
        pass
        # noinspection PyUnresolvedReferences
        # from . import types
