from . import models


def resolve_product_types(info, **_kwargs):
    return models.ProductType.objects.all()
