from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = "anphene.products"

    def ready(self):
        # noinspection PyUnresolvedReferences
        pass
