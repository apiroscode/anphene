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
from ..dataloaders import (
    CollectionsByProductIdLoader,
    ImagesByProductIdLoader,
    ProductByIdLoader,
    ImagesByProductVariantIdLoader,
    ProductVariantsByProductIdLoader,
    SelectedAttributesByProductIdLoader,
    SelectedAttributesByProductVariantIdLoader,
)
from ..utils.availability import get_product_availability, get_variant_availability
from ..utils.sku import generate_sku
from ...attributes.types import SelectedAttribute
from ...collections.types import Collection
from ...core.permissions import ProductPermissions
from ...discounts.dataloaders import DiscountsByDateTimeLoader


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
    variants = graphene.List(
        lambda: ProductVariant, description="List of variants for the product."
    )
    images = graphene.List(lambda: ProductImage, description="List of images for the product.")
    collections = graphene.List(
        lambda: Collection, description="List of collections for the product."
    )

    get_unique_sku = graphene.String(description="Only used in variants generator.")

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
            "updated_at",
            "is_published",
            "publication_date",
            "seo_title",
            "seo_description",
        ]

    @staticmethod
    def resolve_thumbnail(root: models.Product, info, *, size=255):
        def return_first_thumbnail(images):
            image = images[0] if images else None
            if image:
                url = get_product_image_thumbnail(image, size, method="thumbnail")
                alt = image.alt
                return Image(alt=alt, url=info.context.build_absolute_uri(url))
            return None

        return ImagesByProductIdLoader(info.context).load(root.id).then(return_first_thumbnail)

    @staticmethod
    def resolve_pricing(root: models.Product, info):
        context = info.context
        variants = ProductVariantsByProductIdLoader(context).load(root.id)
        collections = CollectionsByProductIdLoader(context).load(root.id)

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_variants(variants):
                def calculate_pricing_with_collections(collections):
                    availability = get_product_availability(
                        product=root,
                        variants=variants,
                        collections=collections,
                        discounts=discounts,
                    )
                    return ProductPricingInfo(**asdict(availability))

                return collections.then(calculate_pricing_with_collections)

            return variants.then(calculate_pricing_with_variants)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

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
    def resolve_attributes(root: models.Product, info):
        return SelectedAttributesByProductIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_image_by_id(root: models.Product, info, id):
        pk = get_database_id(info, id, ProductImage)
        try:
            return root.images.get(pk=pk)
        except models.ProductImage.DoesNotExist:
            raise GraphQLError("Product image not found.")

    @staticmethod
    def resolve_images(root: models.Product, info, **_kwargs):
        return ImagesByProductIdLoader(info.context).load(root.id)

    @staticmethod
    def resolve_variants(root: models.Product, info, **_kwargs):
        return ProductVariantsByProductIdLoader(info.context).load(root.id)

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="collections")
    def resolve_collections(root: models.Product, *_args):
        return root.collections.all()

    @staticmethod
    def resolve_get_unique_sku(root: models.Product, *_args, **_kwargs):
        return generate_sku(root.name, root.id)


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
            "name",
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
    def resolve_pricing(root: models.ProductVariant, info):
        context = info.context
        product = ProductByIdLoader(context).load(root.product_id)
        collections = CollectionsByProductIdLoader(context).load(root.product_id)

        def calculate_pricing_info(discounts):
            def calculate_pricing_with_product(product):
                def calculate_pricing_with_collections(collections):
                    availability = get_variant_availability(
                        variant=root,
                        product=product,
                        collections=collections,
                        discounts=discounts,
                    )
                    return VariantPricingInfo(**asdict(availability))

                return collections.then(calculate_pricing_with_collections)

            return product.then(calculate_pricing_with_product)

        return (
            DiscountsByDateTimeLoader(context)
            .load(info.context.request_time)
            .then(calculate_pricing_info)
        )

    @staticmethod
    def resolve_product(root: models.ProductVariant, info):
        return ProductByIdLoader(info.context).load(root.product_id)

    @staticmethod
    def resolve_attributes(root: models.ProductVariant, info):
        return SelectedAttributesByProductVariantIdLoader(info.context).load(root.id)

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
    def resolve_images(root: models.ProductVariant, info, *_kwargs):
        return ImagesByProductVariantIdLoader(info.context).load(root.id)

    @classmethod
    def get_node(cls, info, pk):
        user = info.context.user
        visible_products = models.Product.objects.visible_to_user(
            user, ProductPermissions.MANAGE_PRODUCTS
        ).values_list("pk", flat=True)
        qs = cls._meta.model.objects.filter(product__id__in=visible_products)
        return qs.filter(pk=pk).first()


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
