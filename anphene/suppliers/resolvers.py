from .models import Supplier


def resolve_suppliers(_info, **_kwargs):
    return Supplier.objects.all()
