from typing import List

import django_filters
from django.db.models import Q
from django.utils import timezone

from core.graph.filters import ListObjectTypeFilter, ObjectTypeFilter
from core.graph.types import FilterInputObjectType
from core.graph.types.common import DateTimeRangeInput, IntRangeInput
from core.utils.filters import filter_fields_containing_value, filter_range_field
from . import DiscountType
from .enums import DiscountStatusEnum, DiscountTypeEnum, VoucherDiscountType
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


def filter_discount_type(
    qs: VoucherQueryset, _, value: List[VoucherDiscountType]
) -> VoucherQueryset:
    if value:
        query = Q()
        if VoucherDiscountType.FIXED in value:
            query |= Q(
                discount_type=VoucherDiscountType.FIXED.value  # type: ignore
            )
        if VoucherDiscountType.PERCENTAGE in value:
            query |= Q(
                discount_type=VoucherDiscountType.PERCENTAGE.value  # type: ignore
            )
        if VoucherDiscountType.SHIPPING in value:
            query |= Q(type=VoucherDiscountType.SHIPPING)
        qs = qs.filter(query).distinct()
    return qs


def filter_started(qs, _, value):
    return filter_range_field(qs, "start_date", value)


def filter_sale_type(qs, _, value):
    if value in [DiscountType.FIXED, DiscountType.PERCENTAGE]:
        qs = qs.filter(type=value)
    return qs


class VoucherFilter(django_filters.FilterSet):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(input_class=IntRangeInput, method=filter_times_used)

    discount_type = ListObjectTypeFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
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
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    search = django_filters.CharFilter(
        method=filter_fields_containing_value("name", "value", "type")
    )

    class Meta:
        model = Sale
        fields = ["status", "sale_type", "started", "search"]


class SaleFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SaleFilter
