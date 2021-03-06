from . import models


def resolve_categories(_info, level=None, **_kwargs):
    qs = models.Category.tree.all()
    if level is not None:
        qs = qs.filter(level=level)
    return qs.distinct()
