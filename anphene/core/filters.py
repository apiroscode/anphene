from core.graph.utils import get_nodes
from core.utils.filters import (
    filter_by_exclude_ids,
    filter_by_include_ids,
)
from ..discounts import types as discount_types


def filter_sales(qs, _, value):
    if value:
        sales = get_nodes(value, discount_types.Sale)
        qs = filter_by_include_ids(qs, sales, "sale")
    return qs


def filter_not_in_sales(qs, _, value):
    if value:
        sales = get_nodes(value, discount_types.Sale)
        qs = filter_by_exclude_ids(qs, sales, "sale")
    return qs


def filter_vouchers(qs, _, value):
    if value:
        vouchers = get_nodes(value, discount_types.Voucher)
        qs = filter_by_include_ids(qs, vouchers, "voucher")
    return qs


def filter_not_in_vouchers(qs, _, value):
    if value:
        vouchers = get_nodes(value, discount_types.Voucher)
        qs = filter_by_exclude_ids(qs, vouchers, "voucher")
    return qs
