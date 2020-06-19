import uuid

from django.core.exceptions import ValidationError

from .models import Voucher


class InvalidPromoCode(ValidationError):
    def __init__(self, message=None, **kwargs):
        if message is None:
            message = {
                "promo_code": ValidationError(
                    "Promo code is invalid", code=GiftCardErrorCode.INVALID
                )
            }
        super().__init__(message, **kwargs)


class PromoCodeAlreadyExists(ValidationError):
    def __init__(self, message=None, **kwargs):
        code = kwargs.get("code", GiftCardErrorCode.ALREADY_EXISTS)
        if message is None:
            message = {"promo_code": ValidationError("Promo code already exists.", code=code)}
        super().__init__(message, **kwargs)


def generate_promo_code():
    """Generate a promo unique code that can be used as a voucher or gift card code."""
    code = str(uuid.uuid4()).replace("-", "").upper()[:12]
    while not is_available_promo_code(code):
        code = str(uuid.uuid4()).replace("-", "").upper()[:12]
    return code


def is_available_promo_code(code):
    return not (promo_code_is_voucher(code))


def promo_code_is_voucher(code):
    return Voucher.objects.filter(code=code).exists()
