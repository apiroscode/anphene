import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from core.graph.mutations import (
    ModelDeleteMutation,
    ModelMutation,
)
from core.graph.types import Upload
from core.utils.images import validate_image_file
from core.utils.urls import validate_storefront_url
from .. import models
from ..emails import send_set_password_email_with_url
from ...core.permissions import UserPermissions


class StaffInput(graphene.InputObjectType):
    email = graphene.String(description="The unique email address of the user.")
    is_active = graphene.Boolean(description="User account is active.", required=False,)
    note = graphene.String(description="A note about the user.", required=False)
    name = graphene.String(description="Name of staff.")
    id_card = Upload(description="ID Card.", required=False)
    groups = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of permission group IDs to which user should be assigned.",
        required=False,
    )


class StaffCreateInput(StaffInput):
    redirect_url = graphene.String(
        description=(
            "URL of a view where users should be redirected to "
            "set the password. URL in RFC 1808 format."
        )
    )


class StaffCreate(ModelMutation):
    class Arguments:
        input = StaffCreateInput(
            description="Fields required to create a staff user.", required=True
        )

    class Meta:
        description = "Creates a new staff user."
        exclude = ["password"]
        model = models.User
        permissions = (UserPermissions.MANAGE_STAFF,)

    @classmethod
    @transaction.atomic
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        groups = cleaned_data.get("groups")
        if groups:
            instance.groups.set(groups)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        redirect_url = cleaned_input.get("redirect_url")
        if redirect_url:
            try:
                validate_storefront_url(redirect_url)
            except ValidationError as error:
                raise ValidationError({"redirect_url": error})

        if data.get("id_card"):
            image_data = info.context.FILES.get(data["id_card"])
            validate_image_file(image_data, "id_card")

        # set is_staff to True to create a staff user
        cleaned_input["is_staff"] = True

        return cleaned_input

    @classmethod
    def save(cls, info, user, cleaned_input):
        redirect_url = cleaned_input.get("redirect_url")
        user.save()
        if redirect_url:
            send_set_password_email_with_url(
                redirect_url=cleaned_input.get("redirect_url"), user=user, staff=True
            )


class StaffUpdate(StaffCreate):
    class Arguments:
        id = graphene.ID(description="ID of a staff user to update.", required=True)
        input = StaffInput(description="Fields required to create a staff user.", required=True)

    class Meta:
        description = "Updates an existing staff user."
        exclude = ["password"]
        model = models.User
        permissions = (UserPermissions.MANAGE_STAFF,)


class StaffDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a staff user to delete.")

    class Meta:
        description = "Deletes a staff user."
        model = models.User
        permissions = (UserPermissions.MANAGE_STAFF,)
