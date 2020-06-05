from . import models


def resolve_attributes(info, qs=None, in_category=None, in_collection=None, **_kwargs):
    qs = qs or models.Attribute.objects.get_visible_to_user(info.context.user)

    # if in_category:
    #     qs = filter_attributes_by_product_types(qs, "in_category", in_category)
    #
    # if in_collection:
    #     qs = filter_attributes_by_product_types(qs, "in_collection", in_collection)

    return qs.distinct()
