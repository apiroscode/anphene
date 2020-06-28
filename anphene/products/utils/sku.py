from ..models import ProductVariant


def generate_sku(name, product_id=None):
    sku = name[0:3].upper()
    unique_sku = sku
    qs = ProductVariant.objects.filter(sku__istartswith=unique_sku)
    if product_id:
        qs = qs.exclude(product_id=product_id)
    sku_checker = qs.exists()

    extension = 0
    while sku_checker:
        extension += 1
        unique_sku = f"{sku}{extension}"
        qs = ProductVariant.objects.filter(sku__istartswith=unique_sku)
        if product_id:
            qs = qs.exclude(product_id=product_id)
        sku_checker = qs.exists()

    return unique_sku
