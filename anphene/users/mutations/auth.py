import graphene
from django.contrib.auth import login, logout, password_validation, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext as _

from core.graph.mutations import BaseMutation, validation_error_to_error_type
from core.graph.types import Error
from core.utils.urls import validate_storefront_url
from .. import models
from ..emails import send_user_password_reset_email_with_url
from ..types import User

INVALID_TOKEN = _("Invalid or expired token.")


class Login(BaseMutation):
    user = graphene.Field(User)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    class Meta:
        description = "Login and get login sessions."

    @classmethod
    def mutate(cls, root, info, **kwargs):
        email = kwargs.get("email")
        password = kwargs.get("password")
        user = info.context.user

        if user.is_authenticated:
            return Login(errors=[Error(message=_("User already login."))])

        form = AuthenticationForm(
            request=info.context, data={"username": email, "password": password}
        )

        if not form.is_valid():
            return Login(errors=[Error(message=_("Wrong email / password!"))])

        user = form.get_user()
        login(info.context, user)
        return cls(user=user, errors=[])


class Logout(BaseMutation):
    class Meta:
        description = "Logout and will clear sessions."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        request = info.context
        logout(request)
        return cls()


class SetPassword(BaseMutation):
    user = graphene.Field(User, description="A user instance with new password.")

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        token = graphene.String(
            description="A one-time token required to set the password.", required=True
        )

    class Meta:
        description = (
            "Sets the user's password from the token sent by email "
            "using the RequestPasswordReset mutation."
        )

    @classmethod
    def mutate(cls, root, info, **data):
        email = data["email"]
        password = data["password"]
        token = data["token"]

        try:
            user = cls._set_password_for_user(email, password, token)
        except ValidationError as e:
            errors = validation_error_to_error_type(e)
            return cls(errors=[e[0] for e in errors])
        return cls(user=user, errors=[])

    @classmethod
    def _set_password_for_user(cls, email, password, token):
        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError({"email": ValidationError(_("User doesn't exist"))})
        if not default_token_generator.check_token(user, token):
            raise ValidationError({"token": ValidationError(INVALID_TOKEN)})
        try:
            password_validation.validate_password(password, user)
        except ValidationError as error:
            raise ValidationError({"password": error})
        user.set_password(password)
        user.save(update_fields=["password"])
        return user


class RequestPasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(
            required=True, description="Email of the user that will be used for password recovery."
        )
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "reset the password. URL in RFC 1808 format."
            ),
        )

    class Meta:
        description = "Sends an email with the account password modification link."

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        email = data["email"]
        redirect_url = data["redirect_url"]
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError({"redirect_url": error})

        try:
            user = models.User.objects.get(email=email)
        except ObjectDoesNotExist:
            raise ValidationError(
                {"email": ValidationError(_("User with this email doesn't exist"))}
            )
        send_user_password_reset_email_with_url(redirect_url, user)
        return cls()


class PasswordChange(BaseMutation):
    user = graphene.Field(User, description="A user instance with a new password.")

    class Arguments:
        old_password = graphene.String(required=True, description="Current user password.")
        new_password = graphene.String(required=True, description="New user password.")

    class Meta:
        description = "Change the password of the logged in user."

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        old_password = data["old_password"]
        new_password = data["new_password"]

        if not user.check_password(old_password):
            raise ValidationError(
                {"old_password": ValidationError(_("Old password isn't valid."))}
            )
        try:
            password_validation.validate_password(new_password, user)
        except ValidationError as error:
            raise ValidationError({"new_password": error})

        user.set_password(new_password)
        user.save(update_fields=["password"])
        update_session_auth_hash(info.context, user)
        return cls(user=user)
