from typing import Union

from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models import Case, Count, F, FilteredRelation, Q, Value, When

from core.db.models import PublishedQuerySet
from ..attributes.models import AttributeProduct, AttributeValue
from ..core.permissions import ProductPermissions


class ProductsQueryset(PublishedQuerySet):
    MINIMAL_PRICE_FIELDS = {"minimal_variant_price_amount", "minimal_variant_price"}

    def collection_sorted(self, user):
        qs = self.visible_to_user(user, ProductPermissions.MANAGE_PRODUCTS)
        qs = qs.order_by(
            F("collectionproduct__sort_order").asc(nulls_last=True), F("collectionproduct__id"),
        )
        return qs

    def sort_by_attribute(self, attribute_pk: Union[int, str], descending: bool = False):
        """Sort a query set by the values of the given product attribute.

        :param attribute_pk: The database ID (must be a numeric) of the attribute
                             to sort by.
        :param descending: The sorting direction.
        """
        qs: models.QuerySet = self
        # If the passed attribute ID is valid, execute the sorting
        if not (isinstance(attribute_pk, int) or attribute_pk.isnumeric()):
            return qs.annotate(
                concatenated_values_order=Value(None, output_field=models.IntegerField()),
                concatenated_values=Value(None, output_field=models.CharField()),
            )

        # Retrieve all the products' attribute data IDs (assignments) and
        # product types that have the given attribute associated to them
        associated_values = tuple(
            AttributeProduct.objects.filter(attribute_id=attribute_pk).values_list(
                "pk", "product_type_id"
            )
        )

        if not associated_values:
            qs = qs.annotate(
                concatenated_values_order=Value(None, output_field=models.IntegerField()),
                concatenated_values=Value(None, output_field=models.CharField()),
            )

        else:
            attribute_associations, product_types_associated_to_attribute = zip(*associated_values)

            qs = qs.annotate(
                # Contains to retrieve the attribute data (singular) of each product
                # Refer to `AttributeProduct`.
                filtered_attribute=FilteredRelation(
                    relation_name="attributes",
                    condition=Q(attributes__assignment_id__in=attribute_associations),
                ),
                # Implicit `GROUP BY` required for the `StringAgg` aggregation
                grouped_ids=Count("id"),
                # String aggregation of the attribute's values to efficiently sort them
                concatenated_values=Case(
                    # If the product has no association data but has
                    # the given attribute associated to its product type,
                    # then consider the concatenated values as empty (non-null).
                    When(
                        Q(product_type_id__in=product_types_associated_to_attribute)
                        & Q(filtered_attribute=None),
                        then=models.Value(""),
                    ),
                    default=StringAgg(
                        F("filtered_attribute__values__name"),
                        delimiter=",",
                        ordering=(
                            [
                                f"filtered_attribute__values__{field_name}"
                                for field_name in AttributeValue._meta.ordering or []
                            ]
                        ),
                    ),
                    output_field=models.CharField(),
                ),
                concatenated_values_order=Case(
                    # Make the products having no such attribute be last in the sorting
                    When(concatenated_values=None, then=2),
                    # Put the products having an empty attribute value at the bottom of
                    # the other products.
                    When(concatenated_values="", then=1),
                    # Put the products having an attribute value to be always at the top
                    default=0,
                    output_field=models.IntegerField(),
                ),
            )

        # Sort by concatenated_values_order then
        # Sort each group of products (0, 1, 2, ...) per attribute values
        # Sort each group of products by name,
        # if they have the same values or not values
        ordering = "-" if descending else ""
        return qs.order_by(
            f"{ordering}concatenated_values_order",
            f"{ordering}concatenated_values",
            f"{ordering}name",
        )


class ProductVariantQueryset(models.QuerySet):
    def create(self, **kwargs):
        """Create a product's variant.

        After the creation update the "minimal_variant_price" of the product.
        """
        variant = super().create(**kwargs)

        from .tasks import update_product_minimal_variant_price_task

        update_product_minimal_variant_price_task.delay(variant.product_id)
        return variant

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        """Insert each of the product's variant instances into the database.

        After the creation update the "minimal_variant_price" of all the products.
        """
        variants = super().bulk_create(
            objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts
        )
        product_ids = set()
        for obj in objs:
            product_ids.add(obj.product_id)
        product_ids = list(product_ids)

        from .tasks import update_products_minimal_variant_prices_of_catalogues_task

        update_products_minimal_variant_prices_of_catalogues_task.delay(product_ids=product_ids)
        return variants

    def annotate_available_quantity(self):
        return self.annotate(available_quantity=F("quantity") - F("quantity_allocated"))
