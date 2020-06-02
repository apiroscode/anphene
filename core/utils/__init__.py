from django.db.models import Value
from django.db.models.functions import Concat
from ..graph.enums import PermissionEnum


def format_permissions_for_display(permissions):
    from ..graph.types import Permission

    """Transform permissions queryset into Permission list.

    Keyword Arguments:
        permissions - queryset with permissions

    """
    permissions_data = permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values("name", "formated_codename")

    formatted_permissions = [
        Permission(code=PermissionEnum.get(data["formated_codename"]), name=data["name"])
        for data in permissions_data
    ]
    return formatted_permissions
