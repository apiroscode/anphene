from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from core.graph.mutations import (
    BaseBulkMutation,
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelMutation,
)
from .. import models
from ..mutations.products import (
    AttributeAssignmentMixin,
    AttributeValueInput,
    ProductVariantCreate,
    ProductVariantInput,
)
from ..types.products import Product, ProductVariant
from ..utils.attributes import (
    generate_name_for_variant,
    get_used_variants_attribute_values,
)
from ...core.permissions import ProductPermissions


class ProductBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product IDs to delete."
        )

    class Meta:
        description = "Deletes products."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)


class ProductBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of products IDs to publish."
        )
        is_published = graphene.Boolean(
            required=True, description="Determine if products will be published or not."
        )

    class Meta:
        description = "Publish products."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)


class ProductVariantBulkCreateInput(ProductVariantInput):
    attributes = graphene.List(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    sku = graphene.String(required=True, description="Stock keeping unit.")
    weight = graphene.Int(description="Weight of the Product.")
    cost = graphene.Int(description="Product cost.")
    price = graphene.Int(description="Product price.")
    quantity = graphene.Int(
        description="""The total quantity of a product available for
        sale. Note: this field is only used if a product doesn't
        use variants."""
    )


class ProductVariantBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True, default_value=0, description="Returns how many objects were created.",
    )
    product = graphene.Field(Product, description="Product of the created variants.")
    product_variants = graphene.List(
        graphene.NonNull(ProductVariant),
        required=True,
        default_value=[],
        description="List of the created variants.",
    )

    class Arguments:
        variants = graphene.List(
            ProductVariantBulkCreateInput,
            required=True,
            description="Input list of product variants to create.",
        )
        product_id = graphene.ID(
            description="ID of the product to create the variants for.",
            name="product",
            required=True,
        )

    class Meta:
        description = "Creates product variants for a given product."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def clean_variant_input(
        cls, info, instance: models.ProductVariant, data: dict, errors: dict, variant_index: int,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, instance, data, input_cls=ProductVariantBulkCreateInput
        )

        weight = cleaned_input.get("weight")
        if weight and weight < 0:
            raise ValidationError(
                {"weight": ValidationError("Product can't have negative weight.")}
            )

        price = cleaned_input.get("price")
        if price and price < 0:
            raise ValidationError(
                {"price": ValidationError("Product price cannot be lower than 0.")}
            )

        cost = cleaned_input.get("cost")
        if cost and cost < 0:
            raise ValidationError(
                {"cost": ValidationError("Product cost cannot be lower than 0.")}
            )

        quantity = cleaned_input.get("quantity")
        if quantity and quantity < 0:
            raise ValidationError(
                {"quantity": ValidationError("Product quantity cannot be lower than 0.")}
            )

        attributes = cleaned_input.get("attributes")
        if attributes:
            try:
                cleaned_input["attributes"] = ProductVariantCreate.clean_attributes(
                    attributes, data["product_type"]
                )
            except ValidationError as exc:
                exc.params = {"index": variant_index}
                errors["attributes"] = exc

        return cleaned_input

    @classmethod
    def add_indexes_to_errors(cls, index, error, error_dict):
        """Append errors with index in params to mutation error dict."""
        for key, value in error.error_dict.items():
            for e in value:
                if e.params:
                    e.params["index"] = index
                else:
                    e.params = {"index": index}
            error_dict[key].extend(value)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            instance.name = generate_name_for_variant(instance)
            instance.save(update_fields=["name"])

    @classmethod
    def create_variants(cls, info, cleaned_inputs, product, errors):
        instances = []
        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                continue
            try:
                instance = models.ProductVariant()
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)
                instances.append(instance)
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors)
        return instances

    @classmethod
    def validate_duplicated_sku(cls, sku, index, sku_list, errors):
        if sku in sku_list:
            errors["sku"].append(ValidationError("Duplicated SKU.", params={"index": index}))
        sku_list.append(sku)

    @classmethod
    def clean_variants(cls, info, variants, product, errors):
        cleaned_inputs = []
        sku_list = []
        used_attribute_values = get_used_variants_attribute_values(product)
        for index, variant_data in enumerate(variants):
            try:
                ProductVariantCreate.validate_duplicated_attribute_values(
                    variant_data.attributes, used_attribute_values
                )
            except ValidationError as exc:
                errors["attributes"].append(ValidationError(exc.message, params={"index": index}))

            variant_data["product_type"] = product.product_type
            cleaned_input = cls.clean_variant_input(info, None, variant_data, errors, index)

            cleaned_inputs.append(cleaned_input if cleaned_input else None)

            if not variant_data.sku:
                continue
            cls.validate_duplicated_sku(variant_data.sku, index, sku_list, errors)
        return cleaned_inputs

    @classmethod
    @transaction.atomic
    def save_variants(cls, info, instances, cleaned_inputs):
        assert len(instances) == len(
            cleaned_inputs
        ), "There should be the same number of instances and cleaned inputs."
        for instance, cleaned_input in zip(instances, cleaned_inputs):
            cls.save(info, instance, cleaned_input)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        product = cls.get_node_or_error(info, data["product_id"], models.Product)
        errors = defaultdict(list)

        cleaned_inputs = cls.clean_variants(info, data["variants"], product, errors)
        instances = cls.create_variants(info, cleaned_inputs, product, errors)
        if errors:
            raise ValidationError(errors)
        cls.save_variants(info, instances, cleaned_inputs)

        return ProductVariantBulkCreate(
            count=len(instances), product_variants=instances, product=product
        )


class ProductVariantBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product variant IDs to delete.",
        )

    class Meta:
        description = "Deletes product variants."
        model = models.ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)


class ProductImageBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of product image IDs to delete.",
        )

    class Meta:
        description = "Deletes product images."
        model = models.ProductImage
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
