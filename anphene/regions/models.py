from django.db import models

from . import CityType


class Province(models.Model):
    name = models.CharField(max_length=256)

    class Meta:
        ordering = ["name"]


class City(models.Model):
    province = models.ForeignKey(Province, related_name="cities", on_delete=models.PROTECT)
    type = models.CharField(max_length=12, choices=CityType.TYPE)
    name = models.CharField(max_length=256, db_index=True)

    class Meta:
        ordering = ["name"]

    @property
    def city_name(self):
        return f"{self.get_type_display()} {self.name}".strip()


class SubDistrict(models.Model):
    city = models.ForeignKey(City, related_name="sub_districts", on_delete=models.PROTECT)
    name = models.CharField(max_length=256, db_index=True)

    class Meta:
        ordering = ["name"]

    def get_full_name(self):
        """
        Bandung Kulon, Kota Bandung - Jawa Barat
        """
        return f"{self.name}, {self.city.city_name} - {self.city.province.name}"
