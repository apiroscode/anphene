import graphene
from django.core.exceptions import ValidationError

from core.graph.mutations import (
    ModelDeleteMutation,
    ModelMutation,
)
from . import models
from .enums import DiscountTypeEnum, VoucherTypeEnum
from .promo_code import generate_promo_code, is_available_promo_code
from ..core.permissions import DiscountPermissions


class VoucherInput(graphene.InputObjectType):
    type = VoucherTypeEnum(description="Voucher type: PRODUCT, CATEGORY SHIPPING or ENTIRE_ORDER.")
    code = graphene.String(description="Code to use the voucher.")
    usage_limit = graphene.Int(
        description="Limit number of times this voucher can be used in total."
    )
    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )

    apply_once_per_order = graphene.Boolean(
        description="Voucher should be applied to the cheapest item or entire order."
    )
    apply_once_per_customer = graphene.Boolean(
        description="Voucher should be applied once per customer."
    )

    discount_type = DiscountTypeEnum(description="Choices: fixed or percentage.")
    discount_value = graphene.Int(description="Value of the voucher.")

    min_spent_amount = graphene.Int(
        description="Min purchase amount required to apply the voucher."
    )
    min_checkout_items_quantity = graphene.Int(
        description="Minimal quantity of checkout items required to apply the voucher."
    )

    products = graphene.List(
        graphene.ID, description="Products discounted by the voucher.", name="products"
    )
    collections = graphene.List(
        graphene.ID, description="Collections discounted by the voucher.", name="collections",
    )
    categories = graphene.List(
        graphene.ID, description="Categories discounted by the voucher.", name="categories",
    )


class VoucherCreate(ModelMutation):
    class Arguments:
        input = VoucherInput(required=True, description="Fields required to create a voucher.")

    class Meta:
        description = "Creates a new voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        code = data.get("code", None)
        if code == "":
            data["code"] = generate_promo_code()
        elif not is_available_promo_code(code):
            raise ValidationError({"code": ValidationError("Promo code already exists.")})
        cleaned_input = super().clean_input(info, instance, data)

        return cleaned_input


class VoucherUpdate(VoucherCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to update.")
        input = VoucherInput(required=True, description="Fields required to update a voucher.")

    class Meta:
        description = "Updates a voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class VoucherDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher to delete.")

    class Meta:
        description = "Deletes a voucher."
        model = models.Voucher
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class SaleInput(graphene.InputObjectType):
    name = graphene.String(description="Voucher name.")
    type = DiscountTypeEnum(description="Fixed or percentage.")
    value = graphene.Int(description="Value of the voucher.")

    start_date = graphene.types.datetime.DateTime(
        description="Start date of the voucher in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="End date of the voucher in ISO 8601 format."
    )

    products = graphene.List(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = graphene.List(
        graphene.ID, description="Categories related to the discount.", name="categories",
    )
    collections = graphene.List(
        graphene.ID, description="Collections related to the discount.", name="collections",
    )


class SaleCreate(ModelMutation):
    class Arguments:
        input = SaleInput(required=True, description="Fields required to create a sale.")

    class Meta:
        description = "Creates a new sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class SaleUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to update.")
        input = SaleInput(required=True, description="Fields required to update a sale.")

    class Meta:
        description = "Updates a sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)


class SaleDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to delete.")

    class Meta:
        description = "Deletes a sale."
        model = models.Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
