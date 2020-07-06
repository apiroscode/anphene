import django_filters

from core.graph.filters import EnumFilter, ObjectTypeFilter
from core.graph.types import FilterInputObjectType
from core.graph.types.common import DateRangeInput
from core.utils.filters import filter_fields_containing_value, filter_range_field
from .enums import StaffMemberStatus
from .models import User


def filter_date_joined(qs, _, value):
    return filter_range_field(qs, "date_joined__date", value)


def filter_status(qs, _, value):
    if value == StaffMemberStatus.ACTIVE:
        qs = qs.filter(is_staff=True, is_active=True)
    elif value == StaffMemberStatus.DEACTIVATED:
        qs = qs.filter(is_staff=True, is_active=False)
    return qs


class CustomerFilter(django_filters.FilterSet):
    date_joined = ObjectTypeFilter(input_class=DateRangeInput, method=filter_date_joined)
    search = django_filters.CharFilter(method=filter_fields_containing_value("name", "email"))

    class Meta:
        model = User
        fields = [
            "date_joined",
            "search",
        ]


class GroupFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))


class StaffUserFilter(django_filters.FilterSet):
    search_fields = (
        "email",
        "name",
    )

    status = EnumFilter(input_class=StaffMemberStatus, method=filter_status)
    search = django_filters.CharFilter(method=filter_fields_containing_value(*search_fields))

    class Meta:
        model = User
        fields = ["status", "search"]


class CustomerFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CustomerFilter


class GroupFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = GroupFilter


class StaffUserInput(FilterInputObjectType):
    class Meta:
        filterset_class = StaffUserFilter
