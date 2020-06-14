import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q

from core.graph.mutations import (
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.utils import from_global_id_strict_type
from core.graph.utils.reordering import perform_reordering
from .. import models
from ..types.product_types import ProductType
from ...attributes import AttributeInputType, models as attributes_models
from ...attributes.enums import AttributeTypeEnum
from ...attributes.mutations import ReorderInput
from ...attributes.types import Attribute
from ...core.permissions import ProductPermissions


class ProductTypeInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Name of the product type.")
    slug = graphene.String(description="Product type slug.")
    has_variants = graphene.Boolean(
        description=(
            "Determines if product of this type has multiple variants. This option "
            "mainly simplifies product management in the dashboard. There is always at "
            "least one variant created under the hood."
        )
    )
    product_attributes = graphene.List(
        graphene.ID,
        description="List of attributes shared among all product variants.",
        name="productAttributes",
    )
    variant_attributes = graphene.List(
        graphene.ID,
        description=(
            "List of attributes used to distinguish between different variants of " "a product."
        ),
        name="variantAttributes",
    )


class ProductTypeCreate(ModelMutation):
    class Arguments:
        input = ProductTypeInput(
            required=True, description="Fields required to create a product type."
        )

    class Meta:
        description = "Creates a new product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCT_TYPES,)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        if "product_attributes" in cleaned_data:
            instance.product_attributes.set(cleaned_data["product_attributes"])
        if "variant_attributes" in cleaned_data:
            instance.variant_attributes.set(cleaned_data["variant_attributes"])


class ProductTypeUpdate(ProductTypeCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to update.")
        input = ProductTypeInput(
            required=True, description="Fields required to update a product type."
        )

    class Meta:
        description = "Updates an existing product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCT_TYPES,)


class ProductTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to delete.")

    class Meta:
        description = "Deletes a product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCT_TYPES,)


class ProductTypeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product type IDs to delete."
        )

    class Meta:
        description = "Deletes product types."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCT_TYPES,)


class ProductTypeReorderAttributes(BaseMutation):
    product_type = graphene.Field(
        ProductType, description="Product type from which attributes are reordered."
    )

    class Meta:
        description = "Reorder the attributes of a product type."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    class Arguments:
        product_type_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a product type."
        )
        type = AttributeTypeEnum(required=True, description="The attribute type to reorder.")
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of attribute reordering operations.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, product_type_id, type, moves):
        pk = from_global_id_strict_type(
            product_type_id, only_type=ProductType, field="product_type_id"
        )

        if type == AttributeTypeEnum.PRODUCT:
            m2m_field = "attributeproduct"
        else:
            m2m_field = "attributevariant"

        try:
            product_type = models.ProductType.objects.prefetch_related(m2m_field).get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_type_id": ValidationError(
                        f"Couldn't resolve to a product type: {product_type_id}",
                    )
                }
            )

        attributes_m2m = getattr(product_type, m2m_field)
        operations = {}

        # Resolve the attributes
        for move_info in moves:
            attribute_pk = from_global_id_strict_type(
                move_info.id, only_type=Attribute, field="moves"
            )

            try:
                m2m_info = attributes_m2m.get(attribute_id=int(attribute_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute: {move_info.id}",
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(attributes_m2m, operations)
        return ProductTypeReorderAttributes(product_type=product_type)


# ATTRIBUTE ASSIGN FOR PRODUCT TYPES
# ==================================
class AttributeAssignInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the attribute to assign.")
    type = AttributeTypeEnum(required=True, description="The attribute type to be assigned as.")


class AttributeAssign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True, description="ID of the product type to assign the attributes into.",
        )
        operations = graphene.List(
            AttributeAssignInput, required=True, description="The operations to perform.",
        )

    class Meta:
        description = "Assign attributes to a given product type."

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(ProductPermissions.MANAGE_PRODUCT_TYPES)

    @classmethod
    def get_operations(cls, info, operations):
        """Resolve all passed global ids into integer PKs of the Attribute type."""
        product_attrs_pks = []
        variant_attrs_pks = []

        for operation in operations:
            pk = from_global_id_strict_type(operation.id, only_type=Attribute, field="operations")
            if operation.type == AttributeTypeEnum.PRODUCT:
                product_attrs_pks.append(pk)
            else:
                variant_attrs_pks.append(pk)

        return product_attrs_pks, variant_attrs_pks

    @classmethod
    def check_operations_not_assigned_already(
        cls, product_type, product_attrs_pks, variant_attrs_pks
    ):
        qs = (
            attributes_models.Attribute.objects.get_assigned_attributes(product_type.pk)
            .values_list("name", "slug")
            .filter(Q(pk__in=product_attrs_pks) | Q(pk__in=variant_attrs_pks))
        )

        invalid_attributes = list(qs)
        if invalid_attributes:
            msg = ", ".join([f"{name} ({slug})" for name, slug in invalid_attributes])
            raise ValidationError(
                {
                    "operations": ValidationError(
                        f"{msg} have already been assigned to this product type.",
                    )
                }
            )

        # check if attributes' input type is assignable to variants
        is_not_assignable_to_variant = attributes_models.Attribute.objects.filter(
            Q(pk__in=variant_attrs_pks)
            & Q(input_type__in=AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS)
        ).exists()

        if is_not_assignable_to_variant:
            raise ValidationError(
                {
                    "operations": ValidationError(
                        (
                            f"Attributes having for input types "
                            f"{AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS} "
                            f"cannot be assigned as variant attributes"
                        ),
                    )
                }
            )

    @classmethod
    def clean_operations(cls, product_type, product_attrs_pks, variant_attrs_pks):
        """Ensure the attributes are not already assigned to the product type."""
        attrs_pk = product_attrs_pks + variant_attrs_pks
        attributes = attributes_models.Attribute.objects.filter(id__in=attrs_pk).values_list(
            "pk", flat=True
        )
        if len(attrs_pk) != len(attributes):
            invalid_attrs = set(attrs_pk) - set(attributes)
            invalid_attrs = [graphene.Node.to_global_id("Attribute", pk) for pk in invalid_attrs]
            raise ValidationError(
                {
                    "operations": ValidationError(
                        "Attribute doesn't exist.", params={"attributes": list(invalid_attrs)},
                    )
                }
            )
        cls.check_operations_not_assigned_already(
            product_type, product_attrs_pks, variant_attrs_pks
        )

    @classmethod
    def save_field_values(cls, product_type, model_name, pks):
        """Add in bulk the PKs to assign to a given product type."""
        model = getattr(attributes_models, model_name)
        for pk in pks:
            model.objects.create(product_type=product_type, attribute_id=pk)

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, **data):
        product_type_id = data["product_type_id"]
        operations = data["operations"]
        # Retrieve the requested product type
        product_type: models.ProductType = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )

        # Resolve all the passed IDs to ints
        product_attrs_pks, variant_attrs_pks = cls.get_operations(info, operations)

        if variant_attrs_pks and not product_type.has_variants:
            raise ValidationError(
                {"operations": ValidationError("Variants are disabled in this product type.",)}
            )

        # Ensure the attribute are assignable
        cls.clean_operations(product_type, product_attrs_pks, variant_attrs_pks)

        # Commit
        cls.save_field_values(product_type, "AttributeProduct", product_attrs_pks)
        cls.save_field_values(product_type, "AttributeVariant", variant_attrs_pks)

        return cls(product_type=product_type)


class AttributeUnassign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True, description="ID of the product type to assign the attributes into.",
        )
        attribute_ids = graphene.List(
            graphene.ID, required=True, description="The IDs of the attributes to unassign.",
        )

    class Meta:
        description = "Un-assign attributes from a given product type."

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(ProductPermissions.MANAGE_PRODUCT_TYPES)

    @classmethod
    def save_field_values(cls, product_type, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(product_type, field).remove(*pks)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        product_type_id = data["product_type_id"]
        attribute_ids = data["attribute_ids"]
        # Retrieve the requested product type
        product_type = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )

        # Resolve all the passed IDs to ints
        attribute_pks = [
            from_global_id_strict_type(attribute_id, only_type=Attribute, field="attribute_id")
            for attribute_id in attribute_ids
        ]

        # Commit
        cls.save_field_values(product_type, "product_attributes", attribute_pks)
        cls.save_field_values(product_type, "variant_attributes", attribute_pks)

        return cls(product_type=product_type)
