from dataclasses import dataclass
from typing import Iterable, Optional

from .. import ProductAvailabilityStatus
from ..models import Product, ProductVariant
from ...collections.models import Collection
from ...core.data import MoneyRange
from ...discounts import DiscountInfo
from ...discounts.utils import calculate_discounted_price


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


def get_product_availability_status(product: "Product") -> ProductAvailabilityStatus:
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


def _get_total_discount_from_range(
    undiscounted: MoneyRange, discounted: MoneyRange
) -> Optional[int]:
    """Calculate the discount amount between two TaxedMoneyRange.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    return _get_total_discount(undiscounted.start, discounted.start)


def _get_total_discount(undiscounted: int, discounted: int) -> Optional[int]:
    """Calculate the discount amount between two TaxedMoney.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    if undiscounted > discounted:
        return undiscounted - discounted
    return None


def get_variant_price(
    *,
    variant: ProductVariant,
    product: Product,
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
):
    return calculate_discounted_price(
        product=product, price=variant.price, collections=collections, discounts=discounts,
    )


def get_product_price_range(
    *,
    product: Product,
    variants: Iterable[ProductVariant],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
) -> MoneyRange:
    prices = [
        get_variant_price(
            variant=variant, product=product, collections=collections, discounts=discounts,
        )
        for variant in variants
    ]
    return MoneyRange(min(prices), max(prices))


def get_product_availability(
    *,
    product: Product,
    variants: Iterable[ProductVariant],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
) -> ProductAvailability:

    if len(variants) <= 0:
        return ProductAvailability(
            on_sale=False,
            price_range=MoneyRange(start=0, stop=0),
            price_range_undiscounted=MoneyRange(start=0, stop=0),
            discount=0,
        )

    discounted = get_product_price_range(
        product=product, variants=variants, collections=collections, discounts=discounts,
    )
    undiscounted = get_product_price_range(
        product=product, variants=variants, collections=collections, discounts=[]
    )

    discount = _get_total_discount_from_range(undiscounted, discounted)

    is_on_sale = product.is_visible and discount is not None
    return ProductAvailability(
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        discount=discount,
    )


def get_variant_availability(
    variant: ProductVariant,
    product: Product,
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
) -> VariantAvailability:
    discounted = get_variant_price(
        variant=variant, product=product, collections=collections, discounts=discounts,
    )
    undiscounted = get_variant_price(
        variant=variant, product=product, collections=collections, discounts=[]
    )

    discount = _get_total_discount(undiscounted, discounted)

    is_on_sale = product.is_visible and discount is not None

    return VariantAvailability(
        on_sale=is_on_sale, price=discounted, price_undiscounted=undiscounted, discount=discount,
    )
