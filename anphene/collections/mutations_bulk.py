import graphene
from django.db import transaction

from core.graph.mutations import (
    BaseBulkMutation,
    BaseMutation,
    ModelBulkDeleteMutation,
)
from . import models
from .types import Collection
from ..core.permissions import CollectionPermissions
from ..products.types.products import Product


class CollectionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of collection IDs to delete."
        )

    class Meta:
        description = "Deletes collections."
        model = models.Collection
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)


class CollectionBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of collections IDs to (un)publish.",
        )
        is_published = graphene.Boolean(
            required=True, description="Determine if collections will be published or not.",
        )

    class Meta:
        description = "Publish collections."
        model = models.Collection
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)

    @classmethod
    def bulk_action(cls, queryset, is_published):
        queryset.update(is_published=is_published)


class CollectionAddProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection to which products will be added."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = graphene.List(graphene.ID, required=True, description="List of product IDs.")

    class Meta:
        description = "Adds products to a collection."
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(products, "products", Product)
        collection.products.add(*products)

        return CollectionAddProducts(collection=collection)


class CollectionRemoveProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products will be removed."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = graphene.List(graphene.ID, required=True, description="List of product IDs.")

    class Meta:
        description = "Remove products from a collection."
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(products, "products", only_type=Product)
        collection.products.remove(*products)

        return CollectionRemoveProducts(collection=collection)
