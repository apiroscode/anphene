from dataclasses import dataclass
from typing import Iterable

from .. import ProductAvailabilityStatus
from ..models import Product, ProductVariant
from ...core.data import MoneyRange


@dataclass
class ProductAvailability:
    on_sale: bool
    price_range: MoneyRange
    price_range_undiscounted: MoneyRange
    discount: int


@dataclass
class VariantAvailability:
    on_sale: bool
    price: int
    price_undiscounted: int
    discount: int


def get_product_availability_status(product: "Product", country: str) -> ProductAvailabilityStatus:
    variants_available_quantity = product.variants.annotate_available_quantity().values_list(
        "available_quantity", flat=True
    )

    is_visible = product.is_visible
    are_all_variants_in_stock = all(variants_available_quantity)
    is_in_stock = any(variants_available_quantity)
    requires_variants = product.product_type.has_variants

    if not product.is_published:
        return ProductAvailabilityStatus.NOT_PUBLISHED
    if requires_variants and not product.variants.exists():
        # We check the requires_variants flag here in order to not show this
        # status with product types that don't require variants, as in that
        # case variants are hidden from the UI and user doesn't manage them.
        return ProductAvailabilityStatus.VARIANTS_MISSSING
    if not is_in_stock:
        return ProductAvailabilityStatus.OUT_OF_STOCK
    if not are_all_variants_in_stock:
        return ProductAvailabilityStatus.LOW_STOCK
    if not is_visible and product.publication_date is not None:
        return ProductAvailabilityStatus.NOT_YET_AVAILABLE
    return ProductAvailabilityStatus.READY_FOR_PURCHASE


def get_product_availability(product: Product, discounts=None) -> ProductAvailability:
    discounted = product.get_price_range(discounts)
    prices = [variant.price for variant in product.variants.all()]
    undiscounted = MoneyRange(min(prices), max(prices))
    discount = (
        undiscounted.start - discounted.start if undiscounted.start > discounted.start else 0
    )

    is_on_sale = product.is_visible and discount != 0
    return ProductAvailability(
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        discount=discount,
    )


def get_variant_availability(
    variant: ProductVariant, product: Product, discounts=None
) -> VariantAvailability:
    discounted = variant.get_price(discounts)
    undiscounted = variant.price
    discount = undiscounted - discounted if undiscounted > discounted else 0

    is_on_sale = product.is_visible and discount != 0

    return VariantAvailability(
        on_sale=is_on_sale, price=discounted, price_undiscounted=undiscounted, discount=discount,
    )
