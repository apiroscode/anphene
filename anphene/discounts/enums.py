import graphene

from . import DiscountType, VoucherType


class DiscountTypeEnum(graphene.Enum):
    FIXED = DiscountType.FIXED
    PERCENTAGE = DiscountType.PERCENTAGE


class VoucherTypeEnum(graphene.Enum):
    SHIPPING = VoucherType.SHIPPING
    ENTIRE_ORDER = VoucherType.ENTIRE_ORDER
    SPECIFIC_PRODUCT = VoucherType.SPECIFIC_PRODUCT


class DiscountStatusEnum(graphene.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"
