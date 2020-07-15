from django.apps import AppConfig


class CheckoutsConfig(AppConfig):
    name = "anphene.checkouts"

    def ready(self):
        # noinspection PyUnresolvedReferences
        # from . import types
        pass
