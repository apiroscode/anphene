from collections import defaultdict

from core.graph.dataloader import DataLoader
from .models import City, Province, SubDistrict


class ProvinceByIdLoader(DataLoader):
    context_key = "province_by_id"

    def batch_load(self, keys):
        provinces = Province.objects.in_bulk(keys)
        return [provinces.get(province_id) for province_id in keys]


class CityByIdLoader(DataLoader):
    context_key = "city_by_id"

    def batch_load(self, keys):
        cities = City.objects.in_bulk(keys)
        return [cities.get(city_id) for city_id in keys]


class SubDistrictByIdLoader(DataLoader):
    context_key = "sub_district_by_id"

    def batch_load(self, keys):
        sub_districts = SubDistrict.objects.in_bulk(keys)
        return [sub_districts.get(district_id) for district_id in keys]


class CityByProvinceIdLoader(DataLoader):
    context_key = "cities_by_province"

    def batch_load(self, keys):
        cities = City.objects.filter(province_id__in=keys)
        city_map = defaultdict(list)
        city_loader = CityByIdLoader(self.context)
        for city in cities.iterator():
            city_map[city.province_id].append(city)
            city_loader.prime(city.id, city)
        return [city_map.get(province_id, []) for province_id in keys]


class SubDistrictByCityIdLoader(DataLoader):
    context_key = "sub_districts_by_city"

    def batch_load(self, keys):
        districts = SubDistrict.objects.filter(city_id__in=keys)
        district_map = defaultdict(list)
        district_loader = SubDistrictByIdLoader(self.context)
        for district in districts.iterator():
            district_map[district.city_id].append(district)
            district_loader.prime(district.id, district)
        return [district_map.get(city_id, []) for city_id in keys]
