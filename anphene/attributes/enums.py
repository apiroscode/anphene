import graphene

from core.graph.enums import to_enum
from . import AttributeInputType

AttributeInputTypeEnum = to_enum(AttributeInputType)


class AttributeTypeEnum(graphene.Enum):
    PRODUCT = "PRODUCT"
    VARIANT = "VARIANT"


class AttributeValueType(graphene.Enum):
    COLOR = "COLOR"
    GRADIENT = "GRADIENT"
    URL = "URL"
    STRING = "STRING"
