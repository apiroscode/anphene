import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import PrefetchingConnectionField
from core.graph.types import Image
from . import models
from ..products import models as products_models
from ..products.types.products import Product


class Category(CountableDjangoObjectType):
    ancestors = PrefetchingConnectionField(
        lambda: Category, description="List of ancestors of the category."
    )
    products = PrefetchingConnectionField(Product, description="List of products in the category.")
    children = PrefetchingConnectionField(
        lambda: Category, description="List of children of the category."
    )
    background_image = graphene.Field(Image, size=graphene.Int(description="Size of the image."))

    class Meta:
        description = (
            "Represents a single category of products. Categories allow to organize "
            "products in a tree-hierarchies which can be used for navigation in the "
            "storefront."
        )
        only_fields = [
            "id",
            "description",
            "level",
            "name",
            "parent",
            "seo_description",
            "seo_title",
            "slug",
        ]
        interfaces = [relay.Node]
        model = models.Category

    @staticmethod
    def resolve_ancestors(root: models.Category, _info, **_kwargs):
        return root.get_ancestors()

    @staticmethod
    def resolve_background_image(root: models.Category, info, size=None, **_kwargs):
        if root.background_image:
            return Image.get_adjusted(
                image=root.background_image,
                alt=root.background_image_alt,
                size=size,
                rendition_key_set="background_images",
                info=info,
            )

    @staticmethod
    @gql_optimizer.resolver_hints(prefetch_related="children")
    def resolve_children(root: models.Category, _info, **_kwargs):
        return root.children.all()

    @staticmethod
    def resolve_products(root: models.Category, info, **_kwargs):
        tree = root.get_descendants(include_self=True)
        qs = products_models.Product.objects.published()
        return qs.filter(category__in=tree)
