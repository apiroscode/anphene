import graphene
from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import PrefetchingConnectionField
from core.graph.types import Image
from . import models
from ..core.permissions import CollectionPermissions


class Collection(CountableDjangoObjectType):
    products = PrefetchingConnectionField(
        "anphene.products.types.products.Product",
        description="List of products in this collection.",
    )
    background_image = graphene.Field(Image, size=graphene.Int(description="Size of the image."))

    class Meta:
        description = "Represents a collection of products."
        only_fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_published",
            "publication_date",
            "seo_description",
            "seo_title",
        ]
        interfaces = [relay.Node]
        model = models.Collection

    @staticmethod
    def resolve_background_image(root: models.Collection, info, size=None, **_kwargs):
        if root.background_image:
            return Image.get_adjusted(
                image=root.background_image,
                alt=root.background_image_alt,
                size=size,
                rendition_key_set="background_images",
                info=info,
            )

    @staticmethod
    def resolve_products(root: models.Collection, info, **_kwargs):
        return root.products.collection_sorted(info.context.user)

    @classmethod
    def get_node(cls, info, id):
        if info.context:
            user = info.context.user
            qs = cls._meta.model.objects.visible_to_user(
                user, CollectionPermissions.MANAGE_COLLECTIONS
            )
            return qs.filter(id=id).first()
        return None
