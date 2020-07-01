import graphene

from core.graph.fields import FilterInputConnectionField, PrefetchingConnectionField
from core.graph.utils import get_node_or_slug
from .filters import ProductFilterInput, ProductTypeFilterInput
from .mutations.product_types import (
    AttributeAssign,
    AttributeUnassign,
    ProductTypeCreate,
    ProductTypeDelete,
    ProductTypeReorderAttributes,
    ProductTypeUpdate,
)
from .mutations.products import (
    ProductCreate,
    ProductDelete,
    ProductImageCreate,
    ProductImageDelete,
    ProductImageReorder,
    ProductImageUpdate,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantDelete,
    ProductVariantUpdate,
    VariantImageAssign,
    VariantImageUnassign,
)
from .mutations.sku import GenerateSKU
from .mutations_bulk.product_types import ProductTypeBulkDelete
from .mutations_bulk.products import (
    ProductBulkDelete,
    ProductBulkPublish,
    ProductImageBulkDelete,
    ProductVariantBulkCreate,
    ProductVariantBulkDelete,
)
from .resolvers import resolve_product_types, resolve_product_variants, resolve_products
from .sorters import ProductSortingInput, ProductTypeSortingInput
from .types.product_types import ProductType
from .types.products import Product, ProductVariant


class ProductQueries(graphene.ObjectType):
    product_type = graphene.Field(
        ProductType,
        id=graphene.Argument(graphene.ID, description="ID of the product type.", required=True),
        description="Look up a product type by ID.",
    )
    product_types = FilterInputConnectionField(
        ProductType,
        filter=ProductTypeFilterInput(description="Filtering options for product types."),
        sort_by=ProductTypeSortingInput(description="Sort product types."),
        description="List of the shop's product types.",
    )

    product = graphene.Field(
        Product,
        id=graphene.Argument(graphene.ID, description="ID of the product.", required=True),
        description="Look up a product by ID.",
    )

    products = FilterInputConnectionField(
        Product,
        filter=ProductFilterInput(description="Filtering options for products."),
        sort_by=ProductSortingInput(description="Sort products."),
        description="List of the shop's products.",
    )

    product_variant = graphene.Field(
        ProductVariant,
        id=graphene.Argument(graphene.ID, description="ID of the product variant.", required=True),
        description="Look up a product variant by ID.",
    )
    product_variants = PrefetchingConnectionField(
        ProductVariant,
        ids=graphene.List(graphene.ID, description="Filter product variants by given IDs."),
        description="List of product variants.",
    )

    def resolve_product_type(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductType)

    def resolve_product_types(self, info, **kwargs):
        return resolve_product_types(info, **kwargs)

    def resolve_product(self, info, id):
        return get_node_or_slug(info, id, Product)

    def resolve_products(self, info, **kwargs):
        return resolve_products(info, **kwargs)

    def resolve_product_variant(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductVariant)

    def resolve_product_variants(self, info, ids=None, **_kwargs):
        return resolve_product_variants(info, ids)


class ProductMutations(graphene.ObjectType):
    # Product Types mutations
    product_type_create = ProductTypeCreate.Field()
    product_type_update = ProductTypeUpdate.Field()
    product_type_delete = ProductTypeDelete.Field()
    product_type_bulk_delete = ProductTypeBulkDelete.Field()
    product_type_reorder_attribute = ProductTypeReorderAttributes.Field()
    attribute_assign = AttributeAssign.Field()
    attribute_unassign = AttributeUnassign.Field()

    # Product mutations
    product_create = ProductCreate.Field()
    product_update = ProductUpdate.Field()
    product_delete = ProductDelete.Field()
    product_bulk_delete = ProductBulkDelete.Field()
    product_bulk_publish = ProductBulkPublish.Field()

    # Product variant mutations
    product_variant_create = ProductVariantCreate.Field()
    product_variant_update = ProductVariantUpdate.Field()
    product_variant_delete = ProductVariantDelete.Field()
    product_variant_bulk_create = ProductVariantBulkCreate.Field()
    product_variant_bulk_delete = ProductVariantBulkDelete.Field()
    variant_image_assign = VariantImageAssign.Field()
    variant_image_unassign = VariantImageUnassign.Field()

    # Product image mutations
    product_image_create = ProductImageCreate.Field()
    product_image_update = ProductImageUpdate.Field()
    product_image_delete = ProductImageDelete.Field()
    product_image_bulk_delete = ProductImageBulkDelete.Field()
    product_image_reorder = ProductImageReorder.Field()

    # SKU GENERATOR
    product_get_sku = GenerateSKU.Field()
