import graphene
from django.core.exceptions import ValidationError

from core.exceptions import PermissionDenied
from core.graph.mutations import ModelBulkDeleteMutation, ModelDeleteMutation, ModelMutation
from core.graph.types import SeoInput, Upload
from core.graph.utils import clean_seo_fields
from core.utils import validate_slug_and_generate_if_needed
from core.utils.images import validate_image_file
from . import models
from .thumbnails import create_category_background_image_thumbnails
from .types import Category
from .utils import delete_categories
from ..core.permissions import CategoryPermissions


class CategoryInput(graphene.InputObjectType):
    description = graphene.JSONString(description="Category description (JSON).")
    name = graphene.String(description="Category name.")
    slug = graphene.String(description="Category slug.")
    seo = SeoInput(description="Search engine optimization fields.")
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")


class CategoryCreate(ModelMutation):
    class Arguments:
        input = CategoryInput(required=True, description="Fields required to create a category.")
        parent_id = graphene.ID(
            description=(
                "ID of the parent category. If empty, category will be top level category."
            ),
            name="parent",
        )

    class Meta:
        description = "Creates a new category."
        model = models.Category
        permissions = (CategoryPermissions.MANAGE_CATEGORIES,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(instance, "name", cleaned_input)
        except ValidationError as error:
            raise ValidationError({"slug": error})
        parent_id = data["parent_id"]
        if parent_id:
            parent = cls.get_node_or_error(info, parent_id, field="parent", only_type=Category)
            cleaned_input["parent"] = parent
        if data.get("background_image"):
            image_data = info.context.FILES.get(data["background_image"])
            validate_image_file(image_data, "background_image")
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        parent_id = data.pop("parent_id", None)
        data["input"]["parent_id"] = parent_id
        return super().perform_mutation(root, info, **data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get("background_image"):
            create_category_background_image_thumbnails.delay(instance.pk)


class CategoryUpdate(CategoryCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to update.")
        input = CategoryInput(required=True, description="Fields required to update a category.")

    class Meta:
        description = "Updates a category."
        model = models.Category
        permissions = (CategoryPermissions.MANAGE_CATEGORIES,)


class CategoryDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to delete.")

    class Meta:
        description = "Deletes a category."
        model = models.Category
        permissions = (CategoryPermissions.MANAGE_CATEGORIES,)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Category)

        db_id = instance.id

        delete_categories([db_id])

        instance.id = db_id
        return cls.success_response(instance)


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of category IDs to delete."
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        permissions = (CategoryPermissions.MANAGE_CATEGORIES,)

    @classmethod
    def bulk_action(cls, queryset):
        delete_categories(queryset.values_list("pk", flat=True))
