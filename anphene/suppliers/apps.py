from django.apps import AppConfig


class SuppliersConfig(AppConfig):
    name = "anphene.suppliers"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import types
