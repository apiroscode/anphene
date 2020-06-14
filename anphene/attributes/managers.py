from django.db import models
from django.db.models import F, Q

from ..core.permissions import ProductPermissions


class BaseAttributeQuerySet(models.QuerySet):
    @staticmethod
    def user_has_access_to_all(user, perm):
        return user.is_active and user.has_perm(perm)

    def get_public_attributes(self):
        raise NotImplementedError

    def get_visible_to_user(self, user, perm):
        if self.user_has_access_to_all(user, perm):
            return self.all()
        return self.get_public_attributes()


class AssociatedAttributeQuerySet(BaseAttributeQuerySet):
    def get_public_attributes(self):
        return self.filter(attribute__visible_in_storefront=True)


class AttributeQuerySet(BaseAttributeQuerySet):
    def get_unassigned_attributes(self, product_type_pk: int):
        return self.exclude(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    def get_assigned_attributes(self, product_type_pk: int):
        return self.filter(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    def get_public_attributes(self):
        return self.filter(visible_in_storefront=True)

    def _get_sorted_m2m_field(self, m2m_field_name: str, asc: bool):
        sort_order_field = F(f"{m2m_field_name}__sort_order")
        id_field = F(f"{m2m_field_name}__id")
        if asc:
            sort_method = sort_order_field.asc(nulls_last=True)
            id_sort = id_field
        else:
            sort_method = sort_order_field.desc(nulls_first=True)
            id_sort = id_field.desc()

        return self.order_by(sort_method, id_sort)

    def product_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributeproduct", asc)

    def variant_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributevariant", asc)
