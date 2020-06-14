from django.apps import AppConfig


class SiteConfig(AppConfig):
    name = "anphene.site"

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals
