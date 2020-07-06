import graphene
from django.contrib.auth import models as auth_models

from core.graph.enums import PermissionEnum
from core.graph.mutations import (
    BaseMutation,
    ModelBulkDeleteMutation,
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.utils import from_global_id_strict_type
from .. import models
from ..types import Group, User
from ...core.permissions import get_permissions, GroupPermissions, UserPermissions


class GroupInput(graphene.InputObjectType):
    name = graphene.String(description="Group name.", required=False)
    permissions = graphene.List(
        graphene.NonNull(PermissionEnum),
        description="List of permission code names to assign to this group.",
        required=False,
    )


class GroupCreate(ModelMutation):
    group = graphene.Field(Group, description="The newly created group.")

    class Arguments:
        input = GroupInput(description="Input fields to create permission group.", required=True)

    class Meta:
        description = "Create new permission group."
        model = auth_models.Group
        permissions = (GroupPermissions.MANAGE_GROUPS,)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        # clean and prepare permissions
        if "permissions" in cleaned_input:
            cleaned_input["permissions"] = get_permissions(cleaned_input["permissions"])
        return cleaned_input


class GroupUpdate(GroupCreate):
    group = graphene.Field(Group, description="Group which was edited.")

    class Arguments:
        id = graphene.ID(description="ID of the group to update.", required=True)
        input = GroupInput(description="Input fields to create permission group.", required=True)

    class Meta:
        description = "Update permission group."
        model = auth_models.Group
        permissions = (GroupPermissions.MANAGE_GROUPS,)


class GroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(description="ID of the group to delete.", required=True)

    class Meta:
        description = "Delete permission group."
        model = auth_models.Group
        permissions = (GroupPermissions.MANAGE_GROUPS,)


class GroupBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True, description="List of group IDs to delete.")

    class Meta:
        description = "Deletes groups."
        model = auth_models.Group
        permissions = (GroupPermissions.MANAGE_GROUPS,)


class GroupStaffAssign(BaseMutation):
    group = graphene.Field(Group, description="The updated group type.")

    class Arguments:
        group_id = graphene.ID(
            required=True, description="Id of the group type to assign the staff into."
        )
        staff_ids = graphene.List(graphene.ID, required=True, description="Staff ids.")

    class Meta:
        description = "Assign staff to a given group type."

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(UserPermissions.MANAGE_STAFF)

    @classmethod
    def save_field_values(cls, group, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(group, field).add(*pks)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        group_id = data["group_id"]
        staff_ids = data["staff_ids"]

        # Retrieve the requested group
        group = graphene.Node.get_node_from_global_id(info, group_id, only_type=Group)

        # Resolve all the passed IDs to ints
        raw_staff_pks = [
            from_global_id_strict_type(staff_id, only_type=User, field="staff_id")
            for staff_id in staff_ids
        ]
        staff_pks = (
            models.User.objects.staff().filter(id__in=raw_staff_pks,).values_list("pk", flat=True)
        )
        # Commit
        cls.save_field_values(group, "user_set", staff_pks)

        return cls(group=group)


class GroupStaffUnassign(GroupStaffAssign):
    class Meta:
        description = "Unassign staff to a given group type."

    @classmethod
    def save_field_values(cls, group, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(group, field).remove(*pks)
