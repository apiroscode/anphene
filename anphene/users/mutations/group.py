import graphene
from django.contrib.auth import models as auth_models

from anphene.core.permissions import get_permissions, GroupPermissions
from core.graph.enums import PermissionEnum
from core.graph.mutations import ModelBulkDeleteMutation, ModelDeleteMutation, ModelMutation
from ..types import Group


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
