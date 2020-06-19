from dataclasses import dataclass
from typing import List, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    # flake8: noqa
    from .models import Sale, Voucher


class DiscountType:
    FIXED = "fixed"
    PERCENTAGE = "percentage"

    CHOICES = [
        (FIXED, "RP"),
        (PERCENTAGE, "%"),
    ]


class VoucherType:
    SHIPPING = "shipping"
    ENTIRE_ORDER = "entire_order"
    SPECIFIC_PRODUCT = "specific_product"

    CHOICES = [
        (ENTIRE_ORDER, "Entire order"),
        (SHIPPING, "Shipping"),
        (SPECIFIC_PRODUCT, "Specific products, collections and categories"),
    ]


@dataclass
class DiscountInfo:
    sale: Union["Sale", "Voucher"]
    product_ids: Union[List[int], Set[int]]
    category_ids: Union[List[int], Set[int]]
    collection_ids: Union[List[int], Set[int]]
