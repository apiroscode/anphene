import os
import re
from functools import reduce

from django.utils.deconstruct import deconstructible


@deconstructible
class UploadToPathAndRename(object):
    """
    Upload to path and rename for image field use in django model
    """

    def __init__(self, path, field):
        self.path = path
        self.field = field

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]

        # get value from field and remove all symbols and whitespace
        name = reduce(getattr, self.field.split("."), instance)
        name = re.sub(r"[^\w]", "", str(name))

        filename = f"{name}.{ext}"
        filename = "".join(filename.split())

        return os.path.join(self.path, filename)
