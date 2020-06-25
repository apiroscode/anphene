from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, TYPE_CHECKING

from ...core.data import MoneyRange

if TYPE_CHECKING:
    from ..models import Product, ProductVariant


@dataclass
class CostsData:
    costs: List[int]
    margins: List[float]

    def __post_init__(self):
        self.costs = sorted(self.costs)
        self.margins = sorted(self.margins)


def get_product_costs_data(product: "Product",) -> Tuple[MoneyRange, Tuple[int, int]]:

    purchase_costs_range = MoneyRange(start=0, stop=0)
    margin = (0, 0)

    if not product.variants.exists():
        return purchase_costs_range, margin

    variants = product.variants.all()
    costs_data = get_cost_data_from_variants(variants)
    if costs_data.costs:
        purchase_costs_range = MoneyRange(min(costs_data.costs), max(costs_data.costs))
    if costs_data.margins:
        margin = (costs_data.margins[0], costs_data.margins[-1])
    return purchase_costs_range, margin


def get_cost_data_from_variants(variants: Iterable["ProductVariant"]) -> CostsData:
    costs: List[int] = []
    margins: List[float] = []
    for variant in variants:
        costs_data = get_variant_costs_data(variant)
        costs += costs_data.costs
        margins += costs_data.margins
    return CostsData(costs, margins)


def get_variant_costs_data(variant: "ProductVariant") -> CostsData:
    costs = []
    margins = []
    costs.append(get_cost_price(variant))
    margin = get_margin_for_variant(variant)
    if margin:
        margins.append(margin)
    return CostsData(costs, margins)


def get_cost_price(variant: "ProductVariant") -> int:
    if not variant.cost:
        return 0
    return variant.cost


def get_margin_for_variant(variant: "ProductVariant") -> Optional[float]:
    if variant.cost == 0:
        return None
    price = variant.price
    margin = price - variant.cost
    percent = round((margin / price) * 100, 0)
    return percent
