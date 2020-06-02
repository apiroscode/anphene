import django_filters

from core.utils.filters import filter_fields_containing_value
from .models import City, SubDistrict


class CityFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))

    class Meta:
        model = City
        fields = ["province", "search"]


class SubDistrictFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_fields_containing_value("name"))

    class Meta:
        model = SubDistrict
        fields = ["city", "search"]
