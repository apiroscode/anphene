from django.utils.translation import ugettext_lazy as _


class CoreError(Exception):
    default_message = None

    def __init__(self, message=None):
        if message is None:
            message = self.default_message

        super(CoreError, self).__init__(message)


class PermissionDenied(CoreError):
    default_message = _("You do not have permission to perform this action")


class ReadOnlyException(CoreError):
    default_message = _("API runs in read-only mode")


class InsufficientStock(Exception):
    def __init__(self, item):
        super().__init__("Insufficient stock for %r" % (item,))
        self.item = item
