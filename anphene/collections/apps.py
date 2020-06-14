from django.apps import AppConfig


class CollectionsConfig(AppConfig):
    name = "anphene.collections"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import types
