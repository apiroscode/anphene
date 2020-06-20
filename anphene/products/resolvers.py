from core.graph.utils import get_database_id
from . import models
from ..core.permissions import ProductPermissions


def resolve_product_types(_info, **_kwargs):
    return models.ProductType.objects.all()


def resolve_products(info, **_kwargs):
    user = info.context.user
    qs = models.Product.objects.visible_to_user(user, ProductPermissions.MANAGE_PRODUCTS)

    return qs.distinct()


def resolve_product_variants(info, ids=None):
    user = info.context.user
    visible_products = models.Product.objects.visible_to_user(
        user, ProductPermissions.MANAGE_PRODUCTS
    ).values_list("pk", flat=True)
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
    if ids:
        db_ids = [get_database_id(info, node_id, "ProductVariant") for node_id in ids]
        qs = qs.filter(pk__in=db_ids)
    return qs


# TODO: After order completed
# def resolve_report_product_sales(period):
#     qs = models.ProductVariant.objects.all()
#
#     # exclude draft and canceled orders
#     exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED]
#     qs = qs.exclude(order_lines__order__status__in=exclude_status)
#
#     # filter by period
#     qs = filter_by_period(qs, period, "order_lines__order__created")
#
#     qs = qs.annotate(quantity_ordered=Sum("order_lines__quantity"))
#     qs = qs.filter(quantity_ordered__isnull=False)
#     return qs.order_by("-quantity_ordered")
