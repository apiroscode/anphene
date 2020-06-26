from ..models import ProductVariant


def generate_sku(name):
    sku = name[0:3].upper()
    unique_sku = sku
    sku_checker = ProductVariant.objects.filter(sku__istartswith=unique_sku).exists()

    extension = 0
    while sku_checker:
        extension += 1
        unique_sku = f"{sku}{extension}"
        sku_checker = ProductVariant.objects.filter(sku__istartswith=unique_sku).exists()

    return unique_sku
