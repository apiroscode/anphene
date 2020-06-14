from .models import Supplier


def resolve_suppliers(info, **_kwargs):
    return Supplier.objects.all()
