from collections import defaultdict
from typing import Iterable, List, Tuple, Union

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.template.defaultfilters import slugify
from graphene import InputObjectType
from graphql_relay import from_global_id

from core.graph.mutations import (
    BaseMutation,
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.types import SeoInput, Upload
from core.graph.utils import clean_seo_fields
from core.utils import validate_slug_and_generate_if_needed
from core.utils.images import validate_image_file
from .. import models
from ..thumbnails import create_product_thumbnails
from ..types.products import Product, ProductImage, ProductVariant
from ..utils.attributes import (
    associate_attribute_values_to_instance,
    generate_name_for_variant,
    get_used_attribute_values_for_variant,
    get_used_variants_attribute_values,
    validate_attribute_input_for_product,
    validate_attribute_input_for_variant,
)
from ...attributes import models as attributes_models
from ...core.permissions import ProductPermissions


class AttributeValueInput(InputObjectType):
    id = graphene.ID(description="ID of the selected attribute.")
    values = graphene.List(
        graphene.String,
        required=True,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )


class ProductInput(graphene.InputObjectType):
    category = graphene.ID(description="ID of the product's category.", name="category")
    supplier = graphene.ID(description="ID of the product's supplier.", name="supplier")
    collections = graphene.List(
        graphene.ID,
        description="List of IDs of collections that the product belongs to.",
        name="collections",
    )

    attributes = graphene.List(AttributeValueInput, description="List of attributes.")

    name = graphene.String(description="Product name.")
    slug = graphene.String(description="Product slug.")
    description = graphene.JSONString(description="Product description (JSON).")

    is_published = graphene.Boolean(description="Determines if product is visible to customers.")
    publication_date = graphene.types.datetime.Date(
        description="Publication date. ISO 8601 standard."
    )
    seo = SeoInput(description="Search engine optimization fields.")

    # SINGLE VARIANTS
    sku = graphene.String(
        description=(
            "Stock keeping unit of a product. Note: this field is only used if "
            "a product doesn't use variants."
        ),
        required=False,
    )
    track_inventory = graphene.Boolean(
        description=(
            "Determines if the inventory of this product should be tracked. If false, "
            "the quantity won't change when customers buy this item. Note: this field "
            "is only used if a product doesn't use variants."
        ),
        required=False,
    )
    weight = graphene.Int(description="Weight of the Product.", required=False)
    cost = graphene.Int(description="Product cost.", required=False)
    price = graphene.Int(description="Product price.", required=False)
    quantity = graphene.Int(
        description="""The total quantity of a product available for
        sale. Note: this field is only used if a product doesn't
        use variants.""",
        required=False,
    )


class ProductCreateInput(ProductInput):
    product_type = graphene.ID(
        description="ID of the type that product belongs to.", name="productType", required=True,
    )


T_INPUT_MAP = List[Tuple[attributes_models.Attribute, List[str]]]
T_INSTANCE = Union[models.Product, models.ProductVariant]


class AttributeAssignmentMixin:
    """Handles cleaning of the attribute input and creating the proper relations.
    1. You should first call ``clean_input``, to transform and attempt to resolve
       the provided input into actual objects. It will then perform a few
       checks to validate the operations supplied by the user are possible and allowed.
    2. Once everything is ready and all your data is saved inside a transaction,
       you shall call ``save`` with the cleaned input to build all the required
       relations. Once the ``save`` call is done, you are safe from continuing working
       or to commit the transaction.
    Note: you shall never call ``save`` outside of a transaction and never before
    the targeted instance owns a primary key. Failing to do so, the relations will
    be unable to build or might only be partially built.
    """

    @classmethod
    def _resolve_attribute_nodes(
        cls, qs: QuerySet, *, global_ids: List[str], pks: Iterable[int], slugs: Iterable[str],
    ):
        """Retrieve attributes nodes from given global IDs and/or slugs."""
        qs = qs.filter(Q(pk__in=pks) | Q(slug__in=slugs))
        nodes = list(qs)  # type: List[attributes_models.Attribute]

        if not nodes:
            raise ValidationError(
                f"Could not resolve to a node: ids={global_ids}" f" and slugs={list(slugs)}",
            )

        nodes_pk_list = set()
        nodes_slug_list = set()
        for node in nodes:
            nodes_pk_list.add(node.pk)
            nodes_slug_list.add(node.slug)

        for pk, global_id in zip(pks, global_ids):
            if pk not in nodes_pk_list:
                raise ValidationError(f"Could not resolve {global_id!r} to Attribute")

        for slug in slugs:
            if slug not in nodes_slug_list:
                raise ValidationError(f"Could not resolve slug {slug!r} to Attribute")

        return nodes

    @classmethod
    def _resolve_attribute_global_id(cls, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        graphene_type, internal_id = from_global_id(global_id)  # type: str, str
        if graphene_type != "Attribute":
            raise ValidationError(f"Must receive an Attribute id, got {graphene_type}.")
        if not internal_id.isnumeric():
            raise ValidationError(f"An invalid ID value was passed: {global_id}")
        return int(internal_id)

    @classmethod
    def _pre_save_values(cls, attribute: attributes_models.Attribute, values: List[str]):
        """Lazy-retrieve or create the database objects from the supplied raw values."""
        get_or_create = attribute.values.get_or_create
        return tuple(
            get_or_create(attribute=attribute, slug=slugify(value), defaults={"name": value})[0]
            for value in values
        )

    @classmethod
    def _check_input_for_product(cls, cleaned_input: T_INPUT_MAP, qs: QuerySet):
        """Check the cleaned attribute input for a product.
        An Attribute queryset is supplied.
        - ensure all required attributes are passed
        - ensure the values are correct for a product
        """
        supplied_attribute_pk = []
        for attribute, values in cleaned_input:
            validate_attribute_input_for_product(attribute, values)
            supplied_attribute_pk.append(attribute.pk)

        # Asserts all required attributes are supplied
        missing_required_filter = Q(value_required=True) & ~Q(pk__in=supplied_attribute_pk)

        if qs.filter(missing_required_filter).exists():
            raise ValidationError(
                "All attributes flagged as having a value required must be supplied."
            )

    @classmethod
    def _check_input_for_variant(cls, cleaned_input: T_INPUT_MAP, qs: QuerySet):
        """Check the cleaned attribute input for a variant.
        An Attribute queryset is supplied.
        - ensure all attributes are passed
        - ensure the values are correct for a variant
        """
        if len(cleaned_input) != qs.count():
            raise ValidationError("All attributes must take a value")

        for attribute, values in cleaned_input:
            validate_attribute_input_for_variant(attribute, values)

    @classmethod
    def _validate_input(cls, cleaned_input: T_INPUT_MAP, attribute_qs, is_variant: bool):
        """Check if no invalid operations were supplied.
        :raises ValidationError: when an invalid operation was found.
        """
        if is_variant:
            return cls._check_input_for_variant(cleaned_input, attribute_qs)
        else:
            return cls._check_input_for_product(cleaned_input, attribute_qs)

    @classmethod
    def clean_input(
        cls, raw_input: dict, attributes_qs: QuerySet, is_variant: bool
    ) -> T_INPUT_MAP:
        """Resolve and prepare the input for further checks.
        :param raw_input: The user's attributes input.
        :param attributes_qs:
            A queryset of attributes, the attribute values must be prefetched.
            Prefetch is needed by ``_pre_save_values`` during save.
        :param is_variant: Whether the input is for a variant or a product.
        :raises ValidationError: contain the message.
        :return: The resolved data
        """

        # Mapping to associate the input values back to the resolved attribute nodes
        pks = {}
        slugs = {}

        # Temporary storage of the passed ID for error reporting
        global_ids = []

        for attribute_input in raw_input:
            global_id = attribute_input.get("id")
            slug = attribute_input.get("slug")
            values = attribute_input["values"]

            if global_id:
                internal_id = cls._resolve_attribute_global_id(global_id)
                global_ids.append(global_id)
                pks[internal_id] = values
            elif slug:
                slugs[slug] = values
            else:
                raise ValidationError("You must whether supply an ID or a slug")

        attributes = cls._resolve_attribute_nodes(
            attributes_qs, global_ids=global_ids, pks=pks.keys(), slugs=slugs.keys()
        )
        cleaned_input = []
        for attribute in attributes:
            key = pks.get(attribute.pk, None)

            # Retrieve the primary key by slug if it
            # was not resolved through a global ID but a slug
            if key is None:
                key = slugs[attribute.slug]

            cleaned_input.append((attribute, key))
        cls._validate_input(cleaned_input, attributes_qs, is_variant)
        return cleaned_input

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input into the database against the given instance.
        Note: this should always be ran inside a transaction.
        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        for attribute, values in cleaned_input:
            values = cls._pre_save_values(attribute, values)
            associate_attribute_values_to_instance(instance, attribute, *values)


class ProductCreate(ModelMutation):
    class Arguments:
        input = ProductCreateInput(
            required=True, description="Fields required to create a product."
        )

    class Meta:
        description = "Creates a new product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def clean_attributes(cls, attributes: dict, product_type: models.ProductType) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_variant=False
        )
        return attributes

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.

        attributes = cleaned_input.get("attributes")
        product_type = (
            instance.product_type if instance.pk else cleaned_input.get("product_type")
        )  # type: models.ProductType

        try:
            cleaned_input = validate_slug_and_generate_if_needed(instance, "name", cleaned_input)
        except ValidationError as error:
            raise ValidationError({"slug": error})

        if attributes and product_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(attributes, product_type)
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        is_published = cleaned_input.get("is_published")
        category = cleaned_input.get("category")
        if not category and is_published:
            raise ValidationError(
                {
                    "isPublished": ValidationError(
                        "You must select a category to be able to publish"
                    )
                }
            )

        clean_seo_fields(cleaned_input)
        cls.clean_single_variants(product_type, cleaned_input)
        cls.clean_sku(product_type, cleaned_input, instance)
        return cleaned_input

    @classmethod
    def clean_sku(cls, product_type, cleaned_input, instance):
        if product_type and not product_type.has_variants:
            input_sku = cleaned_input.get("sku")

            if not input_sku and not instance.pk:
                raise ValidationError({"sku": ValidationError("This field cannot be blank.")})

            if instance.pk:
                exists = (
                    (
                        models.ProductVariant.objects.filter(sku=input_sku)
                        .exclude(product_id=instance.pk)
                        .exists()
                    )
                    if input_sku
                    else False
                )
            else:
                exists = models.ProductVariant.objects.filter(sku=input_sku).exists()

            if exists:
                raise ValidationError(
                    {"sku": ValidationError("Product with this SKU already exists.")}
                )

    @classmethod
    def clean_single_variants(cls, product_type, cleaned_input):
        if product_type and not product_type.has_variants:
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

    @classmethod
    def get_instance(cls, info, **data):
        """Prefetch related fields that are needed to process the mutation."""
        # If we are updating an instance and want to update its attributes,
        # prefetch them.

        object_id = data.get("id")
        if object_id and data.get("attributes"):
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = cls.Meta.model.objects.prefetch_related(
                "product_type__product_attributes__values", "product_type__attributeproduct",
            )
            return cls.get_node_or_error(info, object_id, only_type="Product", qs=qs)

        return super().get_instance(info, **data)

    @classmethod
    @transaction.atomic
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if not instance.product_type.has_variants:
            site_settings = info.context.site.settings
            track_inventory = cleaned_input.get(
                "track_inventory", site_settings.track_inventory_by_default
            )
            quantity = cleaned_input.get("quantity", 0)
            sku = cleaned_input.get("sku")
            weight = cleaned_input.get("weight", 0)
            cost = cleaned_input.get("cost", 0)
            price = cleaned_input.get("price", 0)
            models.ProductVariant.objects.create(
                product=instance,
                sku=sku,
                track_inventory=track_inventory,
                weight=weight,
                cost=cost,
                price=price,
                quantity=quantity,
            )

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        collections = cleaned_data.get("collections", None)
        if collections is not None:
            instance.collections.set(collections)


class ProductUpdate(ProductCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductInput(required=True, description="Fields required to update a product.")

    class Meta:
        description = "Updates an existing product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    @transaction.atomic
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if not instance.product_type.has_variants:
            variant = instance.variants.first()
            update_fields = []
            if "track_inventory" in cleaned_input:
                variant.track_inventory = cleaned_input["track_inventory"]
                update_fields.append("track_inventory")
            if "quantity" in cleaned_input:
                variant.quantity = cleaned_input["quantity"]
                update_fields.append("quantity")
            if "sku" in cleaned_input:
                variant.sku = cleaned_input["sku"]
                update_fields.append("sku")
            if "weight" in cleaned_input:
                variant.weight = cleaned_input["weight"]
                update_fields.append("weight")
            if "cost" in cleaned_input:
                variant.cost = cleaned_input["cost"]
                update_fields.append("cost")
            if "price" in cleaned_input:
                variant.price = cleaned_input["price"]
                update_fields.append("price")
            if update_fields:
                variant.save(update_fields=update_fields)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)


class ProductDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to delete.")

    class Meta:
        description = "Deletes a product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)


class ProductVariantInput(graphene.InputObjectType):
    attributes = graphene.List(
        AttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )
    sku = graphene.String(description="Stock keeping unit.")
    track_inventory = graphene.Boolean(
        description=(
            "Determines if the inventory of this variant should be tracked. If false, "
            "the quantity won't change when customers buy this item."
        )
    )
    weight = graphene.Int(description="Weight of the Product.")
    cost = graphene.Int(description="Product cost.")
    price = graphene.Int(description="Product price.")
    quantity = graphene.Int(
        description="""The total quantity of a product available for
        sale. Note: this field is only used if a product doesn't
        use variants."""
    )


class ProductVariantCreateInput(ProductVariantInput):
    attributes = graphene.List(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    product = graphene.ID(
        description="Product ID of which type is the variant.", name="product", required=True,
    )


class ProductVariantCreate(ModelMutation):
    class Arguments:
        input = ProductVariantCreateInput(
            required=True, description="Fields required to create a product variant."
        )

    class Meta:
        description = "Creates a new variant for a product."
        model = models.ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def clean_attributes(cls, attributes: dict, product_type: models.ProductType) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_variant=True
        )
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes, used_attribute_values, instance=None
    ):
        attribute_values = defaultdict(list)
        for attribute in attributes:
            attribute_values[attribute.id].extend(attribute.values)
        if attribute_values in used_attribute_values:
            raise ValidationError("Duplicated attribute values for product variant.")
        else:
            used_attribute_values.append(attribute_values)

    @classmethod
    def clean_input(cls, info, instance: models.ProductVariant, data: dict):
        cleaned_input = super().clean_input(info, instance, data)

        weight = cleaned_input.get("weight", 0)
        if weight <= 0:
            raise ValidationError(
                {"weight": ValidationError("Product can't have negative weight.")}
            )

        price = cleaned_input.get("price")
        if price and price <= 0:
            raise ValidationError(
                {"price": ValidationError("Product price cannot be lower than 0.")}
            )

        cost = cleaned_input.get("cost")
        if cost and cost < 0:
            raise ValidationError(
                {"cost": ValidationError("Product cost cannot be lower than 0.")}
            )

        quantity = cleaned_input.get("quantity")
        if quantity and quantity <= 0:
            raise ValidationError(
                {"quantity": ValidationError("Product quantity cannot be lower than 0.")}
            )

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.
        attributes = cleaned_input.get("attributes")
        if attributes:
            if instance.product_id is not None:
                # If the variant is getting updated,
                # simply retrieve the associated product type
                product_type = instance.product.product_type
                used_attribute_values = get_used_variants_attribute_values(instance.product)
            else:
                # If the variant is getting created, no product type is associated yet,
                # retrieve it from the required "product" input field
                product_type = cleaned_input["product"].product_type
                used_attribute_values = get_used_variants_attribute_values(
                    cleaned_input["product"]
                )

            try:
                cls.validate_duplicated_attribute_values(
                    attributes, used_attribute_values, instance
                )
                cleaned_input["attributes"] = cls.clean_attributes(attributes, product_type)
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})
        return cleaned_input

    @classmethod
    def get_instance(cls, info, **data):
        """Prefetch related fields that are needed to process the mutation.
        If we are updating an instance and want to update its attributes,
        # prefetch them.
        """

        object_id = data.get("id")
        if object_id and data.get("attributes"):
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = cls.Meta.model.objects.prefetch_related(
                "product__product_type__variant_attributes__values",
                "product__product_type__attributevariant",
            )
            return cls.get_node_or_error(info, object_id, only_type="ProductVariant", qs=qs)

        return super().get_instance(info, **data)

    @classmethod
    @transaction.atomic()
    def save(cls, info, instance, cleaned_input):
        instance.save()

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            instance.name = generate_name_for_variant(instance)
            instance.save(update_fields=["name"])


class ProductVariantUpdate(ProductVariantCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product variant to update.")
        input = ProductVariantInput(
            required=True, description="Fields required to update a product variant."
        )

    class Meta:
        description = "Updates an existing variant for product."
        model = models.ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes, used_attribute_values, instance=None
    ):
        # Check if the variant is getting updated,
        # and the assigned attributes do not change
        if instance.product_id is not None:
            assigned_attributes = get_used_attribute_values_for_variant(instance)
            input_attribute_values = defaultdict(list)
            for attribute in attributes:
                input_attribute_values[attribute.id].extend(attribute.values)
            if input_attribute_values == assigned_attributes:
                return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(attributes, used_attribute_values)


class ProductVariantDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product variant to delete.")

    class Meta:
        description = "Deletes a product variant."
        model = models.ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)


class ProductImageCreateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for an image.")
    image = Upload(required=True, description="Represents an image file in a multipart request.")
    product = graphene.ID(required=True, description="ID of an product.", name="product")


class ProductImageCreate(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        input = ProductImageCreateInput(
            required=True, description="Fields required to create a product image."
        )

    class Meta:
        description = (
            "Create a product image. This mutation must be sent as a `multipart` "
            "request. More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        product = cls.get_node_or_error(info, data["product"], field="product", only_type=Product)
        image_data = info.context.FILES.get(data["image"])
        validate_image_file(image_data, "image")

        image = product.images.create(image=image_data, alt=data.get("alt", ""))
        transaction.on_commit(lambda: create_product_thumbnails.delay(image.pk))
        return ProductImageCreate(product=product, image=image)


class ProductImageUpdateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for an image.")


class ProductImageUpdate(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product image to update.")
        input = ProductImageUpdateInput(
            required=True, description="Fields required to update a product image."
        )

    class Meta:
        description = "Updates a product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        image = cls.get_node_or_error(info, data.get("id"), only_type=ProductImage)
        product = image.product
        alt = data.get("input").get("alt")
        if alt is not None:
            image.alt = alt
            image.save(update_fields=["alt"])
        return ProductImageUpdate(product=product, image=image)


class ProductImageReorder(BaseMutation):
    product = graphene.Field(Product)
    images = graphene.List(ProductImage)

    class Arguments:
        product_id = graphene.ID(
            required=True, description="Id of product that images order will be altered.",
        )
        images_ids = graphene.List(
            graphene.ID,
            required=True,
            description="IDs of a product images in the desired order.",
        )

    class Meta:
        description = "Changes ordering of the product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, product_id, images_ids):
        product = cls.get_node_or_error(info, product_id, field="product_id", only_type=Product)
        if len(images_ids) != product.images.count():
            raise ValidationError(
                {"order": ValidationError("Incorrect number of image IDs provided.")}
            )

        images = []
        for image_id in images_ids:
            image = cls.get_node_or_error(info, image_id, field="order", only_type=ProductImage)
            if image and image.product != product:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Image %(image_id)s does not belong to this product.",
                            params={"image_id": image_id},
                        )
                    }
                )
            images.append(image)

        for order, image in enumerate(images):
            image.sort_order = order
            image.save(update_fields=["sort_order"])

        return ProductImageReorder(product=product, images=images)


class ProductImageDelete(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product image to delete.")

    class Meta:
        description = "Deletes a product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        image = cls.get_node_or_error(info, data.get("id"), only_type=ProductImage)
        image_id = image.id
        image.delete()
        image.id = image_id
        return ProductImageDelete(product=image.product, image=image)


class VariantImageAssign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    image = graphene.Field(ProductImage)

    class Arguments:
        image_id = graphene.ID(
            required=True, description="ID of a product image to assign to a variant."
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Assign an image to a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, image_id, variant_id):
        image = cls.get_node_or_error(info, image_id, field="image_id", only_type=ProductImage)
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant
        )
        if image and variant:
            # check if the given image and variant can be matched together
            image_belongs_to_product = variant.product.images.filter(pk=image.pk).first()
            if image_belongs_to_product:
                image.variant_images.create(variant=variant)
            else:
                raise ValidationError(
                    {"image_id": ValidationError("This image doesn't belong to that product.",)}
                )
        return VariantImageAssign(product_variant=variant, image=image)


class VariantImageUnassign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    image = graphene.Field(ProductImage)

    class Arguments:
        image_id = graphene.ID(
            required=True, description="ID of a product image to unassign from a variant.",
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Unassign an image from a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)

    @classmethod
    def perform_mutation(cls, _root, info, image_id, variant_id):
        image = cls.get_node_or_error(info, image_id, field="image_id", only_type=ProductImage)
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant
        )

        try:
            variant_image = models.VariantImage.objects.get(image=image, variant=variant)
        except models.VariantImage.DoesNotExist:
            raise ValidationError(
                {"image_id": ValidationError("Image is not assigned to this variant.",)}
            )
        else:
            variant_image.delete()

        return VariantImageUnassign(product_variant=variant, image=image)
