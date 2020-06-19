from dataclasses import asdict

import graphene
import graphene_django_optimizer as gql_optimizer
from django.conf import settings
from graphene import relay
from graphql.error import GraphQLError

from core.decorators import permission_required
from core.graph.connection import CountableDjangoObjectType
from core.graph.types import Image, MoneyRange
from core.graph.utils import get_database_id
from core.utils.images import get_product_image_thumbnail, get_thumbnail
from .. import models
from ..utils.availability import get_product_availability, get_variant_availability
from ...attributes import models as attributes_models
from ...attributes.types import SelectedAttribute
from ...collections.types import Collection
from ...core.permissions import ProductPermissions


def resolve_attribute_list(instance, *, user):
    """Resolve attributes from a product into a list of `SelectedAttribute`s.
    Note: you have to prefetch the below M2M fields.
        - product_type -> attribute[rel] -> [rel]assignments -> values
        - product_type -> attribute[rel] -> attribute
    """
    resolved_attributes = []

    # Retrieve the product type
    if isinstance(instance, models.Product):
        product_type = instance.product_type
        product_type_attributes_assoc_field = "attributeproduct"
        assigned_attribute_instance_field = "productassignments"
        assigned_attribute_instance_filters = {"product_id": instance.pk}
    elif isinstance(instance, models.ProductVariant):
        product_type = instance.product.product_type
        product_type_attributes_assoc_field = "attributevariant"
        assigned_attribute_instance_field = "variantassignments"
        assigned_attribute_instance_filters = {"variant_id": instance.pk}
    else:
        raise AssertionError(f"{instance.__class__.__name__} is unsupported")

    # Retrieve all the product attributes assigned to this product type
    attributes_qs = getattr(product_type, product_type_attributes_assoc_field)
    attributes_qs = attributes_qs.get_visible_to_user(user)

    # An empty QuerySet for unresolved values
    empty_qs = attributes_models.AttributeValue.objects.none()

    # Goes through all the attributes assigned to the product type
    # The assigned values are returned as a QuerySet, but will assign a
    # dummy empty QuerySet if no values are assigned to the given instance.
    for attr_data_rel in attributes_qs:
        attr_instance_data = getattr(attr_data_rel, assigned_attribute_instance_field)

        # Retrieve the instance's associated data
        attr_data = attr_instance_data.filter(**assigned_attribute_instance_filters)
        attr_data = attr_data.first()

        # Return the instance's attribute values if the assignment was found,
        # otherwise it sets the values as an empty QuerySet
        values = attr_data.values.all() if attr_data is not None else empty_qs
        resolved_attributes.append(
            SelectedAttribute(attribute=attr_data_rel.attribute, values=values)
        )
    return resolved_attributes


class Margin(graphene.ObjectType):
    start = graphene.Int()
    stop = graphene.Int()


class BasePricingInfo(graphene.ObjectType):
    on_sale = graphene.Boolean(description="Whether it is in sale or not.")
    discount = graphene.Int(description="The discount amount if in sale (null otherwise).")


class VariantPricingInfo(BasePricingInfo):
    price = graphene.Int(description="The price, with any discount subtracted.")
    price_undiscounted = graphene.Int(description="The price without any discount.")

    class Meta:
        description = "Represents availability of a variant in the storefront."


class ProductPricingInfo(BasePricingInfo):
    price_range = graphene.Field(
        MoneyRange, description="The discounted price range of the product variants.",
    )
    price_range_undiscounted = graphene.Field(
        MoneyRange, description="The undiscounted price range of the product variants.",
    )

    class Meta:
        description = "Represents availability of a product in the storefront."


class Product(CountableDjangoObjectType):
    thumbnail = graphene.Field(
        Image,
        description="The main thumbnail for a product.",
        size=graphene.Argument(graphene.Int, description="Size of thumbnail."),
    )
    pricing = graphene.Field(
        ProductPricingInfo,
        description=(
            "Lists the storefront product's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    is_available = graphene.Boolean(
        description="Whether the product is in stock and visible or not."
    )
    attributes = graphene.List(
        graphene.NonNull(SelectedAttribute),
        required=True,
        description="List of attributes assigned to this product.",
    )
    image_by_id = graphene.Field(
        lambda: ProductImage,
        id=graphene.Argument(graphene.ID, description="ID of a product image."),
        description="Get a single product image by ID.",
    )
    variants = gql_optimizer.field(
        graphene.List(lambda: ProductVariant, description="List of variants for the product"),
        model_field="variants",
    )
    images = gql_optimizer.field(
        graphene.List(lambda: ProductImage, description="List of images for the product"),
        model_field="images",
    )
    collections = gql_optimizer.field(
        graphene.List(lambda: Collection, description="List of collections for the product"),
        model_field="collections",
    )

    class Meta:
        description = "Represents an individual item for sale in the storefront."
        interfaces = [relay.Node]
        model = models.Product
        only_fields = [
            "id",
            "supplier",
            "category",
            "product_type",
            "name",
            "slug",
            "description",
            "minimal_variant_price",
            "updated_at",
            "is_published",
            "publication_date",
            "seo_title",
            "seo_description",
        ]

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="images")
    def resolve_thumbnail(root: models.Product, info, *, size=255):
        image = root.get_first_image()
        if image:
            url = get_product_image_thumbnail(image, size, method="thumbnail")
            alt = image.alt
            return Image(alt=alt, url=info.context.build_absolute_uri(url))
        return None

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related=("variants", "collections"))
    def resolve_pricing(root: models.Product, info):
        context = info.context
        availability = get_product_availability(root, context.discounts)
        return ProductPricingInfo(**asdict(availability))

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="variants")
    def resolve_is_available(root: models.Product, info):
        in_stock = any(
            root.variants.annotate_available_quantity().values_list(
                "available_quantity", flat=True
            )
        )
        return root.is_visible and in_stock

    @staticmethod
    @gql_optimizer.resolver_hints(
        prefetch_related=[
            "product_type__attributeproduct__productassignments__values",
            "product_type__attributeproduct__attribute",
        ]
    )
    def resolve_attributes(root: models.Product, info):
        return resolve_attribute_list(root, user=info.context.user)

    @staticmethod
    def resolve_image_by_id(root: models.Product, info, id):
        pk = get_database_id(info, id, ProductImage)
        try:
            return root.images.get(pk=pk)
        except models.ProductImage.DoesNotExist:
            raise GraphQLError("Product image not found.")

    @staticmethod
    @gql_optimizer.resolver_hints(model_field="images")
    def resolve_images(root: models.Product, *_args, **_kwargs):
        return root.images.all()

    @staticmethod
    def resolve_variants(root: models.Product, *_args, **_kwargs):
        return root.variants.all()

    @staticmethod
    def resolve_collections(root: models.Product, *_args):
        return root.collections.all()


class ProductVariant(CountableDjangoObjectType):
    pricing = graphene.Field(
        VariantPricingInfo,
        description=(
            "Lists the storefront variant's pricing, the current price and discounts, "
            "only meant for displaying."
        ),
    )
    attributes = graphene.List(
        graphene.NonNull(SelectedAttribute),
        required=True,
        description="List of attributes assigned to this variant.",
    )
    margin = graphene.Float(description="Gross margin percentage value.")
    quantity_available = graphene.Int(
        required=True, description="Quantity of a product available for sale."
    )
    quantity_ordered = graphene.Int(description="Total quantity ordered.")

    images = gql_optimizer.field(
        graphene.List(lambda: ProductImage, description="List of images for the product variant"),
        model_field="images",
    )
    # TODO: AFTER ORDER APP FINISHED
    # revenue = graphene.Field(
    #     TaxedMoney,
    #     period=graphene.Argument(ReportingPeriod),
    #     description=(
    #         "Total revenue generated by a variant in given period of time. Note: this "
    #         "field should be queried using `reportProductSales` query as it uses "
    #         "optimizations suitable for such calculations."
    #     ),
    # )

    class Meta:
        description = "Represents a version of a product such as different size or color."
        only_fields = [
            "id",
            "product",
            "sku",
            "track_inventory",
            "weight",
            "cost",
            "price",
            "quantity",
            "quantity_allocated",
        ]
        interfaces = [relay.Node]
        model = models.ProductVariant

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related=("product",), only=["price_override"])
    def resolve_pricing(root: models.ProductVariant, info):
        context = info.context
        availability = get_variant_availability(root, root.product, context.discounts,)
        return ProductPricingInfo(**asdict(availability))

    @staticmethod
    @gql_optimizer.resolver_hints(
        prefetch_related=["attributes__values", "attributes__assignment__attribute"]
    )
    def resolve_attributes(root: models.ProductVariant, info):
        return resolve_attribute_list(root, user=info.context.user)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_margin(root: models.ProductVariant, *_args):
        margin = root.price - root.cost
        return round((margin / root.price) * 100, 0)

    @staticmethod
    def resolve_quantity_available(root: models.ProductVariant, _info):
        return min(root.quantity - root.quantity_allocated, settings.MAX_CHECKOUT_LINE_QUANTITY)

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCTS)
    def resolve_quantity_ordered(root: models.ProductVariant, *_args):
        # This field is added through annotation when using the
        # `resolve_report_product_sales` resolver.
        return getattr(root, "quantity_ordered", None)

    @staticmethod
    def resolve_images(root: models.ProductVariant, *_args):
        return root.images.all()


class ProductImage(CountableDjangoObjectType):
    url = graphene.String(
        required=True,
        description="The URL of the image.",
        size=graphene.Int(description="Size of the image."),
    )

    class Meta:
        description = "Represents a product image."
        only_fields = ["alt", "id", "sort_order"]
        interfaces = [relay.Node]
        model = models.ProductImage

    @staticmethod
    def resolve_url(root: models.ProductImage, info, *, size=None):
        if size:
            url = get_thumbnail(root.image, size, method="thumbnail")
        else:
            url = root.image.url
        return info.context.build_absolute_uri(url)
