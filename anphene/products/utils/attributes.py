from collections import defaultdict
from typing import Set, TYPE_CHECKING, Union

import graphene
from django.core.exceptions import ValidationError

from ..models import (
    Product,
    ProductVariant,
)
from ...attributes import AttributeInputType
from ...attributes.models import (
    AssignedProductAttribute,
    AssignedVariantAttribute,
    Attribute,
    AttributeValue,
)

AttributeAssignmentType = Union[AssignedProductAttribute, AssignedVariantAttribute]


if TYPE_CHECKING:
    # flake8: noqa
    from ...attributes.models import AttributeProduct, AttributeVariant


def _associate_attribute_to_instance(
    instance: Union[Product, ProductVariant], attribute_pk: int
) -> AttributeAssignmentType:
    """Associate a given attribute to an instance."""
    assignment: Union["AssignedProductAttribute", "AssignedVariantAttribute"]
    if isinstance(instance, Product):
        attribute_rel: Union[
            "AttributeProduct", "AttributeVariant"
        ] = instance.product_type.attributeproduct.get(attribute_id=attribute_pk)

        assignment, _ = AssignedProductAttribute.objects.get_or_create(
            product=instance, assignment=attribute_rel
        )
    elif isinstance(instance, ProductVariant):
        attribute_rel = instance.product.product_type.attributevariant.get(
            attribute_id=attribute_pk
        )

        assignment, _ = AssignedVariantAttribute.objects.get_or_create(
            variant=instance, assignment=attribute_rel
        )
    else:
        raise AssertionError(f"{instance.__class__.__name__} is unsupported")

    return assignment


def validate_attribute_owns_values(attribute: Attribute, value_ids: Set[int]) -> None:
    """Check given value IDs are belonging to the given attribute.

    :raise: AssertionError
    """
    attribute_actual_value_ids = set(attribute.values.values_list("pk", flat=True))
    found_associated_ids = attribute_actual_value_ids & value_ids
    if found_associated_ids != value_ids:
        raise AssertionError("Some values are not from the provided attribute.")


def associate_attribute_values_to_instance(
    instance: Union[Product, ProductVariant], attribute: Attribute, *values: AttributeValue,
) -> AttributeAssignmentType:
    """Assign given attribute values to a product or variant.

    Note: be award this function invokes the ``set`` method on the instance's
    attribute association. Meaning any values already assigned or concurrently
    assigned will be overridden by this call.
    """
    values_ids = {value.pk for value in values}

    # Ensure the values are actually form the given attribute
    validate_attribute_owns_values(attribute, values_ids)

    # Associate the attribute and the passed values
    assignment = _associate_attribute_to_instance(instance, attribute.pk)
    assignment.values.set(values)
    return assignment


def validate_attribute_input_for_product(instance: "Attribute", values):
    if not values:
        if not instance.value_required:
            return
        raise ValidationError(f"{instance.slug} expects a value but none were given")

    if instance.input_type != AttributeInputType.MULTISELECT and len(values) != 1:
        raise ValidationError(f"A {instance.input_type} attribute must take only one value")

    for value in values:
        if not value.strip():
            raise ValidationError("Attribute values cannot be blank")


def validate_attribute_input_for_variant(instance: "Attribute", values):
    if not values:
        raise ValidationError(f"{instance.slug} expects a value but none were given")

    if len(values) != 1:
        raise ValidationError("A variant attribute cannot take more than one value")

    if not values[0].strip():
        raise ValidationError("Attribute values cannot be blank")


def get_used_attribute_values_for_variant(variant):
    """Create a dict of attributes values for variant.

    Sample result is:
    {
        "attribute_1_global_id": ["ValueAttr1_1"],
        "attribute_2_global_id": ["ValueAttr2_1"]
    }
    """
    attribute_values = defaultdict(list)
    for assigned_variant_attribute in variant.attributes.all():
        attribute = assigned_variant_attribute.attribute
        attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
        for variant in assigned_variant_attribute.values.all():
            attribute_values[attribute_id].append(variant.slug)
    return attribute_values


def get_used_variants_attribute_values(product):
    """Create list of attributes values for all existing `ProductVariants` for product.

    Sample result is:
    [
        {
            "attribute_1_global_id": ["ValueAttr1_1"],
            "attribute_2_global_id": ["ValueAttr2_1"]
        },
        ...
        {
            "attribute_1_global_id": ["ValueAttr1_2"],
            "attribute_2_global_id": ["ValueAttr2_2"]
        }
    ]
    """
    variants = (
        product.variants.prefetch_related("attributes__values")
        .prefetch_related("attributes__assignment")
        .all()
    )
    used_attribute_values = []
    for variant in variants:
        attribute_values = get_used_attribute_values_for_variant(variant)
        used_attribute_values.append(attribute_values)
    return used_attribute_values
