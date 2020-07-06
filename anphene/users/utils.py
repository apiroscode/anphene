from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import Value
from django.db.models.functions import Concat

from . import events as account_events
from ..core.permissions import get_permissions


class UserDeleteMixin:
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        user = info.context.user
        if instance == user:
            raise ValidationError({"id": ValidationError("You cannot delete your own account.",)})
        elif instance.is_superuser:
            raise ValidationError({"id": ValidationError("Cannot delete this account.",)})


class CustomerDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError({"id": ValidationError("Cannot delete a staff account.",)})

        # delete all addresses
        instance.addresses.all().delete()

    @classmethod
    def post_process(cls, info, deleted_count=1):
        account_events.staff_user_deleted_a_customer_event(
            staff_user=info.context.user, deleted_count=deleted_count
        )


def get_user_permissions(user):
    """Return all user permissions - from user groups and user_permissions field."""
    if user.is_superuser:
        return get_permissions()
    groups = user.groups.all()
    user_permissions = user.user_permissions.all()
    group_permissions = Permission.objects.filter(group__in=groups)
    permissions = user_permissions | group_permissions
    return permissions


def get_group_permission_codes(group):
    """Return group permissions in the format '<app label>.<permission codename>'."""
    return group.permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("formated_codename", flat=True)
