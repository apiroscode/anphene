import graphene
from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import PrefetchingConnectionField
from ..categories.types import Category
from ..collections.types import Collection
from ..products.types.products import Product
from .enums import DiscountTypeEnum, VoucherTypeEnum
from . import models
import graphene_django_optimizer as gql_optimizer
from ..core.permissions import CollectionPermissions, ProductPermissions, DiscountPermissions


class Sale(CountableDjangoObjectType):
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category, description="List of categories this sale applies to."
        ),
        model_field="categories",
    )
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection, description="List of collections this sale applies to."
        ),
        model_field="collections",
    )
    products = gql_optimizer.field(
        PrefetchingConnectionField(Product, description="List of products this sale applies to."),
        model_field="products",
    )

    class Meta:
        description = (
            "Sales allow creating discounts for categories, collections or products "
            "and are visible to all the customers."
        )
        interfaces = [relay.Node]
        model = models.Sale
        only_fields = ["end_date", "id", "name", "start_date", "type", "value"]

    @staticmethod
    def resolve_categories(root: models.Sale, *_args, **_kwargs):
        return root.categories.all()

    @staticmethod
    def resolve_collections(root: models.Sale, info, **_kwargs):
        return root.collections.visible_to_user(
            info.context.user, CollectionPermissions.MANAGE_COLLECTIONS
        )

    @staticmethod
    def resolve_products(root: models.Sale, info, **_kwargs):
        return root.products.visible_to_user(info.context.user, ProductPermissions.MANAGE_PRODUCTS)


class Voucher(CountableDjangoObjectType):
    categories = gql_optimizer.field(
        PrefetchingConnectionField(
            Category, description="List of categories this voucher applies to."
        ),
        model_field="categories",
    )
    collections = gql_optimizer.field(
        PrefetchingConnectionField(
            Collection, description="List of collections this voucher applies to."
        ),
        model_field="collections",
    )
    products = gql_optimizer.field(
        PrefetchingConnectionField(
            Product, description="List of products this voucher applies to."
        ),
        model_field="products",
    )

    discount_type = DiscountTypeEnum(
        description="Determines a type of discount for voucher - value or percentage",
        required=True,
    )
    type = VoucherTypeEnum(description="Determines a type of voucher.", required=True)

    class Meta:
        description = (
            "Vouchers allow giving discounts to particular customers on categories, "
            "collections or specific products. They can be used during checkout by "
            "providing valid voucher codes."
        )
        only_fields = [
            "id",
            "type",
            "name",
            "code",
            "usage_limit",
            "used",
            "start_date",
            "end_date",
            "apply_once_per_order",
            "apply_once_per_customer",
            "discount_type",
            "discount_value",
            "min_spent_amount",
            "min_checkout_items_quantity",
        ]
        interfaces = [relay.Node]
        model = models.Voucher

    @staticmethod
    def resolve_categories(root: models.Voucher, *_args, **_kwargs):
        return root.categories.all()

    @staticmethod
    def resolve_collections(root: models.Voucher, info, **_kwargs):
        return root.collections.visible_to_user(
            info.context.user, CollectionPermissions.MANAGE_COLLECTIONS
        )

    @staticmethod
    def resolve_products(root: models.Voucher, info, **_kwargs):
        return root.products.visible_to_user(info.context.user, ProductPermissions.MANAGE_PRODUCTS)
