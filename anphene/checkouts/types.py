import graphene
from graphene import relay

from core.exceptions import PermissionDenied
from core.graph.connection import CountableDjangoObjectType
from core.graph.scalars import UUID
from . import models
from ..core.permissions import UserPermissions


class Checkout(CountableDjangoObjectType):
    token = graphene.Field(UUID, description="The checkout's token.", required=True)
    lines = graphene.List(
        "anphene.checkouts.types.CheckoutLine",
        description=(
            "A list of checkout lines, each containing information about an  item in the checkout."
        ),
    )
    # only show with mutation GetCheckoutInfo
    weight = graphene.Int(description="Total weight.")
    shipping = graphene.Int(description="Shipping cost.")
    shipping_discount = graphene.Int(description="Shipping discount.")
    pay_code = graphene.Int(description="Unique pay code.")
    used_balance = graphene.Int(description="Customer balance to be used.")
    total_lines = graphene.Int(description="Total from lines.")
    total_lines_discount = graphene.Int(
        description="Total discount from lines. (from sale or voucher code)"
    )
    discount = graphene.Int(description="Entire order discount. (using voucher code)")
    total = graphene.Int(description="Shipping cost.")

    class Meta:
        description = "Checkout object."
        model = models.Checkout
        interfaces = [relay.node]

    @staticmethod
    def resolve_user(root: models.Checkout, info):
        user = info.context.user
        if user == root.user or user.has_perm(UserPermissions.MANAGE_CUSTOMERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_lines(root: models.Checkout, info):
        # TODO: after checking it
        pass

    @staticmethod
    def resolve_weight(root: models.Checkout, _info):
        return root.get_total_weight()

    @staticmethod
    def resolve_shipping(root: models.Checkout, _info):
        return getattr(root, "shipping", 0)

    @staticmethod
    def resolve_shipping_discount(root: models.Checkout, _info):
        return getattr(root, "shipping_discount", 0)

    @staticmethod
    def resolve_pay_code(root: models.Checkout, _info):
        return getattr(root, "pay_code", 0)

    @staticmethod
    def resolve_used_balance(root: models.Checkout, _info):
        return getattr(root, "used_balance", 0)

    @staticmethod
    def resolve_total_lines(root: models.Checkout, _info):
        return getattr(root, "total_lines", 0)

    @staticmethod
    def resolve_total_lines_discount(root: models.Checkout, _info):
        return getattr(root, "total_lines_discount", 0)

    @staticmethod
    def resolve_discount(root: models.Checkout, _info):
        return getattr(root, "discount", 0)

    @staticmethod
    def resolve_total(root: models.Checkout, _info):
        return getattr(root, "total", 0)


class CheckoutLine(CountableDjangoObjectType):
    discount = graphene.Int(description="Discount for line, either from sale or voucher code.")

    class Meta:
        description = "Represents an item in the checkout."
        model = models.CheckoutLine
        interfaces = [relay.node]
        only_fields = ["id", "variant", "quantity"]

    @staticmethod
    def resolve_discount(root: models.CheckoutLine, _info):
        return getattr(root, "discount", 0)
