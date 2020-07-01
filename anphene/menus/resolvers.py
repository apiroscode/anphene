from . import models


def resolve_menus(_info, **_kwargs):
    qs = models.Menu.objects.all()
    return qs.distinct()


def resolve_menu_items(_info, **_kwargs):
    qs = models.MenuItem.objects.all()
    return qs.distinct()
