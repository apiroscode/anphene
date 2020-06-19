import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from core.graph.mutations import (
    BaseBulkMutation,
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.types import SeoInput, Upload
from core.graph.utils import clean_seo_fields
from core.utils import validate_slug_and_generate_if_needed
from core.utils.images import validate_image_file
from . import models
from .thumbnails import create_collection_background_image_thumbnails
from .types import Collection
from ..core.permissions import CollectionPermissions
from ..products.tasks import update_products_minimal_variant_prices_of_catalogues_task
from ..products.types.products import Product


class CollectionInput(graphene.InputObjectType):
    is_published = graphene.Boolean(description="Informs whether a collection is published.")
    name = graphene.String(description="Name of the collection.")
    slug = graphene.String(description="Slug of the collection.")
    description = graphene.JSONString(description="Description of the collection (JSON).")
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")
    seo = SeoInput(description="Search engine optimization fields.")
    publication_date = graphene.Date(description="Publication date. ISO 8601 standard.")


class CollectionCreate(ModelMutation):
    class Arguments:
        input = CollectionInput(
            required=True, description="Fields required to create a collection."
        )

    class Meta:
        description = "Creates a new collection."
        model = models.Collection
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(instance, "name", cleaned_input)
        except ValidationError as error:
            raise ValidationError({"slug": error})
        if data.get("background_image"):
            image_data = info.context.FILES.get(data["background_image"])
            validate_image_file(image_data, "background_image")
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get("background_image"):
            create_collection_background_image_thumbnails.delay(instance.pk)


class CollectionUpdate(CollectionCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to update.")
        input = CollectionInput(
            required=True, description="Fields required to update a collection."
        )

    class Meta:
        description = "Updates a collection."
        model = models.Collection
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        if cleaned_input.get("background_image"):
            create_collection_background_image_thumbnails.delay(instance.pk)
        instance.save()


class CollectionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to delete.")

    class Meta:
        description = "Deletes a collection."
        model = models.Collection
        permissions = (CollectionPermissions.MANAGE_COLLECTIONS,)


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
        if collection.sale_set.exists():
            pass
            update_products_minimal_variant_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
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
        if collection.sale_set.exists():
            update_products_minimal_variant_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionRemoveProducts(collection=collection)
