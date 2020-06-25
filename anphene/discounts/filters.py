from typing import List

import django_filters
from django.utils import timezone

from core.graph.filters import ListObjectTypeFilter, ObjectTypeFilter
from core.graph.types import FilterInputObjectType
from core.graph.types.common import DateRangeInput, IntRangeInput
from core.utils.filters import filter_fields_containing_value, filter_range_field
from . import DiscountType, VoucherType
from .enums import DiscountStatusEnum, DiscountTypeEnum, VoucherTypeEnum
from .models import Sale, Voucher, VoucherQueryset


def filter_status(qs: VoucherQueryset, _, value: List[DiscountStatusEnum]) -> VoucherQueryset:
    if not value:
        return qs
    query_objects = qs.none()
    now = timezone.now()
    if DiscountStatusEnum.ACTIVE in value:
        query_objects |= qs.active(now)
    if DiscountStatusEnum.EXPIRED in value:
        query_objects |= qs.expired(now)
    if DiscountStatusEnum.SCHEDULED in value:
        query_objects |= qs.filter(start_date__gt=now)
    return qs & query_objects


def filter_times_used(qs, _, value):
    return filter_range_field(qs, "used", value)


def filter_started(qs, _, value):
    return filter_range_field(qs, "start_date__date", value)


def filter_voucher_type(qs, _, value):
    if value in [VoucherType.SHIPPING, VoucherType.ENTIRE_ORDER, VoucherType.SPECIFIC_PRODUCT]:
        qs = qs.filter(type=value)
    return qs


def filter_discount_type(qs, _, value):
    if value in [DiscountType.FIXED, DiscountType.PERCENTAGE]:
        qs = qs.filter(discount_type=value)
    return qs


def filter_sale_type(qs, _, value):
    if value in [DiscountType.FIXED, DiscountType.PERCENTAGE]:
        qs = qs.filter(type=value)
    return qs


class VoucherFilter(django_filters.FilterSet):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(input_class=IntRangeInput, method=filter_times_used)

    voucher_type = ListObjectTypeFilter(input_class=VoucherTypeEnum, method=filter_voucher_type)
    discount_type = ListObjectTypeFilter(input_class=DiscountTypeEnum, method=filter_discount_type)
    started = ObjectTypeFilter(input_class=DateRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_fields_containing_value("name", "code"))

    class Meta:
        model = Voucher
        fields = ["status", "times_used", "discount_type", "started", "search"]


class VoucherFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = VoucherFilter


class SaleFilter(django_filters.FilterSet):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    sale_type = ObjectTypeFilter(input_class=DiscountTypeEnum, method=filter_sale_type)
    started = ObjectTypeFilter(input_class=DateRangeInput, method=filter_started)
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("name", "value", "type")
    )

    class Meta:
        model = Sale
        fields = ["status", "sale_type", "started", "search"]


class SaleFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SaleFilter
