import graphene
from django.core.exceptions import ValidationError

from core.graph.mutations import (
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.types import SeoInput, Upload
from core.graph.utils import clean_seo_fields
from core.utils import validate_slug_and_generate_if_needed
from core.utils.images import validate_image_file
from . import models
from .thumbnails import create_collection_background_image_thumbnails
from ..core.permissions import CollectionPermissions


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
