from . import models
from ..core.permissions import AttributePermissions


def resolve_attributes(info, in_category=None, in_collection=None, **_kwargs):
    qs = models.Attribute.objects.get_visible_to_user(
        info.context.user, AttributePermissions.MANAGE_ATTRIBUTES
    )

    # if in_category:
    #     qs = filter_attributes_by_product_types(qs, "in_category", in_category)
    #
    # if in_collection:
    #     qs = filter_attributes_by_product_types(qs, "in_collection", in_collection)

    return qs.distinct()
