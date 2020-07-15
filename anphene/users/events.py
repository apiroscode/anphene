from . import CustomerEvents
from .models import CustomerEvent, User


def customer_account_created_event(*, user: User):
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.ACCOUNT_CREATED)


def customer_password_reset_event(*, user: User):
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_RESET)


def customer_password_changed_event(*, user: User):
    return CustomerEvent.objects.create(user=user, type=CustomerEvents.PASSWORD_CHANGED)


def staff_user_assigned_email_to_a_customer_event(*, staff_user: User, new_email: str):
    return CustomerEvent.objects.create(
        user=staff_user, type=CustomerEvents.EMAIL_ASSIGNED, parameters={"message": new_email},
    )


def staff_user_assigned_name_to_a_customer_event(*, staff_user: User, new_name: str):
    return CustomerEvent.objects.create(
        user=staff_user, type=CustomerEvents.NAME_ASSIGNED, parameters={"message": new_name},
    )


def staff_user_deleted_a_customer_event(*, staff_user: User, deleted_count: int = 1):
    return CustomerEvent.objects.create(
        user=staff_user, type=CustomerEvents.CUSTOMER_DELETED, parameters={"count": deleted_count},
    )
