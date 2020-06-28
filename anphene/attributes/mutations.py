import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.template.defaultfilters import slugify

from core.graph.mutations import (
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.utils import from_global_id_strict_type
from core.graph.utils.reordering import perform_reordering
from core.utils import validate_slug_and_generate_if_needed
from . import models
from .enums import AttributeInputTypeEnum
from .types import Attribute, AttributeValue
from ..core.permissions import AttributePermissions


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Name of a value displayed in the interface."
    )
    value = graphene.String(required=False, description="Value of a real value in the interface.")


class AttributeBaseInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Name of an attribute displayed in the interface."
    )
    slug = graphene.String(
        required=False, description="Internal representation of an attribute name."
    )
    value_required = graphene.Boolean(
        description="Whether the attribute requires values to be passed or not."
    )
    visible_in_storefront = graphene.Boolean(
        description="Whether the attribute should be visible or not in storefront."
    )
    filterable_in_storefront = graphene.Boolean(
        description="Whether the attribute can be filtered in storefront."
    )
    filterable_in_dashboard = graphene.Boolean(
        description="Whether the attribute can be filtered in dashboard."
    )
    storefront_search_position = graphene.Int(
        required=False,
        description="The position of the attribute in the storefront navigation (0 by default).",
    )
    available_in_grid = graphene.Boolean(
        required=False,
        description="Whether the attribute can be displayed in the admin product list.",
    )


class AttributeCreateInput(AttributeBaseInput):
    input_type = AttributeInputTypeEnum(
        description="The input type to use for entering attribute values in the dashboard."
    )
    values = graphene.List(AttributeValueCreateInput, description="List of attribute's values.")


class ReorderInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the item to move.")
    sort_order = graphene.Int(
        description="The new relative sorting position of the item (from -inf to +inf)."
    )


class AttributeCreate(ModelMutation):
    attribute = graphene.Field(Attribute, description="The created attribute.")

    class Arguments:
        input = AttributeCreateInput(
            required=True, description="Fields required to create an attribute."
        )

    class Meta:
        model = models.Attribute
        description = "Creates an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)

    @classmethod
    def check_values_are_unique(cls, values_input, attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list("slug", flat=True)
        for value_data in values_input:
            slug = slugify(value_data["name"])
            if slug in existing_values:
                msg = "Value %s already exists within this attribute." % value_data["name"]
                raise ValidationError({"values": ValidationError(msg)})

        new_slugs = [slugify(value_data["name"]) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError({"values": ValidationError("Provided values are not unique.")})

    @classmethod
    def clean_values(cls, cleaned_input, attribute):
        """Clean attribute values.

        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input.get("values")

        if values_input is None:
            return

        for value_data in values_input:
            value_data["slug"] = slugify(value_data["name"])
            attribute_value = models.AttributeValue(**value_data, attribute=attribute)
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field, err in validation_errors.error_dict.items():
                    if field == "attribute":
                        continue
                    raise ValidationError({"values": err})
        cls.check_values_are_unique(values_input, attribute)

    @classmethod
    def clean_attribute(cls, instance, cleaned_input):
        try:
            cleaned_input = validate_slug_and_generate_if_needed(instance, "name", cleaned_input)
        except ValidationError as error:
            raise ValidationError({"slug": error})

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)
        values = cleaned_data.get("values") or []
        for value in values:
            attribute.values.create(**value)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = models.Attribute()

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, data.get("input"))
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeCreate(attribute=instance)


class AttributeUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to update.")
        input = AttributeBaseInput(
            required=True, description="Fields required to update an attribute."
        )

    class Meta:
        model = models.Attribute
        description = "Updates attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to delete.")

    class Meta:
        model = models.Attribute
        description = "Deletes an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of attribute IDs to delete."
        )

    class Meta:
        description = "Deletes attributes."
        model = models.Attribute
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)


# ATTRIBUTE VALUE
# ===============
def validate_value_is_unique(attribute: models.Attribute, value: models.AttributeValue):
    """Check if the attribute value is unique within the attribute it belongs to."""
    duplicated_values = attribute.values.exclude(pk=value.pk).filter(name=value.name)
    if duplicated_values.exists():
        raise ValidationError(
            {"name": ValidationError(f"Value with name {value.name} already exists.")}
        )


class AttributeValueCreate(ModelMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        attribute_id = graphene.ID(
            required=True,
            name="attribute",
            description="Attribute to which value will be assigned.",
        )
        input = AttributeValueCreateInput(
            required=True, description="Fields required to create an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        description = "Creates a value for an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input["slug"] = slugify(cleaned_input["name"])
        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)
        instance = models.AttributeValue(attribute=attribute)
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeValueCreate(attribute=attribute, attributeValue=instance)


class AttributeValueUpdate(ModelMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of an AttributeValue to update.")
        input = AttributeValueCreateInput(
            required=True, description="Fields required to update an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        description = "Updates value of an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" in cleaned_input:
            cleaned_input["slug"] = slugify(cleaned_input["name"])
        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a value to delete.")

    class Meta:
        model = models.AttributeValue
        description = "Deletes a value of an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeReorderValues(BaseMutation):
    attribute = graphene.Field(Attribute, description="Attribute from which values are reordered.")

    class Meta:
        description = "Reorder the values of an attribute."
        permissions = (AttributePermissions.MANAGE_ATTRIBUTES,)

    class Arguments:
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, moves):
        pk = from_global_id_strict_type(attribute_id, only_type=Attribute, field="attribute_id")

        try:
            attribute = models.Attribute.objects.prefetch_related("values").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to an attribute: {attribute_id}"
                    )
                }
            )

        values_m2m = attribute.values
        operations = {}

        # Resolve the values
        for move_info in moves:
            value_pk = from_global_id_strict_type(
                move_info.id, only_type=AttributeValue, field="moves"
            )

            try:
                m2m_info = values_m2m.get(pk=int(value_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute value: {move_info.id}",
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(values_m2m, operations)
        attribute.refresh_from_db(fields=["values"])
        return AttributeReorderValues(attribute=attribute)
