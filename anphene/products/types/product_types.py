import graphene
from graphene import relay

from core.decorators import permission_required
from core.graph.connection import CountableDjangoObjectType
from core.graph.fields import FilterInputConnectionField
from .. import models
from ...attributes import models as attributes_models
from ...attributes.filters import AttributeFilterInput
from ...attributes.resolvers import resolve_attributes
from ...attributes.types import Attribute
from ...core.permissions import ProductPermissions


class ProductType(CountableDjangoObjectType):
    variant_attributes = graphene.List(
        Attribute, description="Variant attributes of that product type."
    )
    product_attributes = graphene.List(
        Attribute, description="Product attributes of that product type."
    )
    available_attributes = FilterInputConnectionField(Attribute, filter=AttributeFilterInput())

    class Meta:
        description = (
            "Represents a type of product. It defines what attributes are available to "
            "products of this type."
        )
        interfaces = [relay.Node]
        model = models.ProductType
        only_fields = ["id", "name", "has_variants"]

    @staticmethod
    def resolve_product_attributes(root: models.ProductType, *_args, **_kwargs):
        return root.product_attributes.product_attributes_sorted().all()

    @staticmethod
    def resolve_variant_attributes(root: models.ProductType, *_args, **_kwargs):
        return root.variant_attributes.variant_attributes_sorted().all()

    @staticmethod
    @permission_required(ProductPermissions.MANAGE_PRODUCT_TYPES)
    def resolve_available_attributes(root: models.ProductType, info, **kwargs):
        qs = attributes_models.Attribute.objects.get_unassigned_attributes(root.pk)
        return resolve_attributes(info, qs=qs, **kwargs)
