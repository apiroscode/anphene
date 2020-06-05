from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat

from ..graph.enums import PermissionEnum

from django.template.defaultfilters import slugify


def format_permissions_for_display(permissions):
    from ..graph.types import Permission

    """Transform permissions queryset into Permission list.

    Keyword Arguments:
        permissions - queryset with permissions

    """
    permissions_data = permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values("name", "formated_codename")

    formatted_permissions = [
        Permission(code=PermissionEnum.get(data["formated_codename"]), name=data["name"])
        for data in permissions_data
    ]
    return formatted_permissions


def generate_unique_slug(
    instance, slugable_value, slug_field_name="slug",
):
    """Create unique slug for model instance.

    The function uses `django.utils.text.slugify` to generate a slug from
    the `slugable_value` of model field. If the slug already exists it adds
    a numeric suffix and increments it until a unique value is found.

    Args:
        instance: model instance for which slug is created
        slugable_value: value used to create slug
        slug_field_name: name of slug field in instance model

    """
    slug = slugify(slugable_value)
    unique_slug = slug

    ModelClass = instance.__class__
    extension = 1

    search_field = f"{slug_field_name}__iregex"
    pattern = rf"{slug}-\d+$|{slug}$"
    slug_values = (
        ModelClass._default_manager.filter(  # type: ignore
            **{search_field: pattern}
        )
        .exclude(pk=instance.pk)
        .values_list(slug_field_name, flat=True)
    )

    while unique_slug in slug_values:
        extension += 1
        unique_slug = f"{slug}-{extension}"

    return unique_slug


def validate_slug_value(cleaned_input, slug_field_name="slug"):
    if slug_field_name in cleaned_input:
        slug = cleaned_input[slug_field_name]
        if not slug:
            raise ValidationError(f"{slug_field_name.capitalize()} value cannot be blank.")


def validate_slug_and_generate_if_needed(
    instance, slugable_field, cleaned_input, slug_field_name="slug",
):
    """Validate slug from input and generate in create mutation if is not given."""

    # update mutation - just check if slug value is not empty
    # _state.adding is True only when it's new not saved instance.
    if not instance._state.adding:  # type: ignore
        validate_slug_value(cleaned_input)
        return cleaned_input

    # create mutation - generate slug if slug value is empty
    slug = cleaned_input.get(slug_field_name)
    if not slug and slugable_field in cleaned_input:
        slug = generate_unique_slug(instance, cleaned_input[slugable_field])
        cleaned_input[slug_field_name] = slug
    return cleaned_input
