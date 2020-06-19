from . import models


def resolve_vouchers(_info, **_kwargs):
    qs = models.Voucher.objects.all()
    return qs


def resolve_sales(_info, **_kwargs):
    qs = models.Sale.objects.all()
    return qs
