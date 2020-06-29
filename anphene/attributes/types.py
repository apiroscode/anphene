import re

import graphene
from graphene import relay

from core.graph.connection import CountableDjangoObjectType
from . import models
from .enums import AttributeInputTypeEnum, AttributeValueType
from ..products.dataloaders import AttributeValuesByAttributeIdLoader

COLOR_PATTERN = r"^(#[0-9a-fA-F]{3}|#(?:[0-9a-fA-F]{2}){2,4}|(rgb|hsl)a?\((-?\d+%?[,\s]+){2,3}\s*[\d\.]+%?\))$"  # noqa
color_pattern = re.compile(COLOR_PATTERN)


def resolve_attribute_value_type(attribute_value):
    if color_pattern.match(attribute_value):
        return AttributeValueType.COLOR
    if "gradient(" in attribute_value:
        return AttributeValueType.GRADIENT
    if "://" in attribute_value:
        return AttributeValueType.URL
    return AttributeValueType.STRING


class Attribute(CountableDjangoObjectType):
    input_type = AttributeInputTypeEnum(
        description="The input type to use for entering attribute values in the dashboard."
    )

    values = graphene.List(
        "anphene.attributes.types.AttributeValue", description="List of attribute's values."
    )

    class Meta:
        description = (
            "Custom attribute of a product. Attributes can be assigned to products and "
            "variants at the product type level."
        )
        only_fields = [
            "id",
            "name",
            "slug",
            "product_types",
            "product_variant_types",
            "value_required",
            "visible_in_storefront",
            "filterable_in_storefront",
            "filterable_in_dashboard",
            "storefront_search_position",
            "available_in_grid",
        ]
        interfaces = [relay.Node]
        model = models.Attribute

    @staticmethod
    def resolve_values(root: models.Attribute, info):
        return AttributeValuesByAttributeIdLoader(info.context).load(root.id)


class AttributeValue(CountableDjangoObjectType):
    type = AttributeValueType(description="Type of value (used only when `value` field is set).")
    input_type = AttributeInputTypeEnum(
        description="The input type to use for entering attribute values in the dashboard."
    )

    class Meta:
        description = "Represents a value of an attribute."
        only_fields = ["id", "name", "slug", "value"]
        interfaces = [relay.Node]
        model = models.AttributeValue

    @staticmethod
    def resolve_type(root: models.AttributeValue, *_args):
        return resolve_attribute_value_type(root.value)

    @staticmethod
    def resolve_input_type(root: models.AttributeValue, *_args):
        return root.input_type


class SelectedAttribute(graphene.ObjectType):
    attribute = graphene.Field(
        Attribute,
        default_value=None,
        description="Name of an attribute displayed in the interface.",
        required=True,
    )
    values = graphene.List(AttributeValue, description="Values of an attribute.", required=True)

    class Meta:
        description = "Represents a custom attribute."


class AttributeInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description="Internal representation of an attribute name."
    )
    values = graphene.List(
        graphene.String,
        required=False,
        description="Internal representation of a value (unique per attribute).",
    )
