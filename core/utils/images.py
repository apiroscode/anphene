import logging
import os
import re
import warnings
from functools import reduce

from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)
register = template.Library()


# cache available sizes at module level
def get_available_sizes():
    rendition_sizes = {}
    keys = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS
    for dummy_size_group, sizes in keys.items():
        rendition_sizes[dummy_size_group] = {size for _, size in sizes}
    return rendition_sizes


AVAILABLE_SIZES = get_available_sizes()


def choose_placeholder(size=""):
    # type: (str) -> str
    """Assign a placeholder at least as big as provided size if possible.

    When size is bigger than available, return the biggest.
    If size is invalid or not provided, return DEFAULT_PLACEHOLDER.
    """
    placeholder = settings.DEFAULT_PLACEHOLDER
    parsed_sizes = re.match(r"(\d+)x(\d+)", size)
    available_sizes = sorted(settings.PLACEHOLDER_IMAGES.keys())
    if parsed_sizes and available_sizes:
        # check for placeholder equal or bigger than requested picture
        x_size, y_size = parsed_sizes.groups()
        max_size = max([int(x_size), int(y_size)])
        bigger_or_eq = list(filter(lambda x: x >= max_size, available_sizes))
        if bigger_or_eq:
            placeholder = settings.PLACEHOLDER_IMAGES[bigger_or_eq[0]]
        else:
            placeholder = settings.PLACEHOLDER_IMAGES[available_sizes[-1]]
    return placeholder


def get_available_sizes_by_method(method, rendition_key_set):
    sizes = []
    for available_size in AVAILABLE_SIZES[rendition_key_set]:
        available_method, avail_size_str = available_size.split("__")
        if available_method == method:
            sizes.append(min([int(s) for s in avail_size_str.split("x")]))
    return sizes


def get_thumbnail_size(size, method, rendition_key_set):
    """Return the closest larger size if not more than 2 times larger.

    Otherwise, return the closest smaller size
    """
    on_demand = settings.VERSATILEIMAGEFIELD_SETTINGS["create_images_on_demand"]
    if isinstance(size, int):
        size_str = "%sx%s" % (size, size)
    else:
        size_str = size
    size_name = "%s__%s" % (method, size_str)
    if size_name in AVAILABLE_SIZES[rendition_key_set] or on_demand:
        return size_str
    avail_sizes = sorted(get_available_sizes_by_method(method, rendition_key_set))
    larger = [x for x in avail_sizes if size < x <= size * 2]
    smaller = [x for x in avail_sizes if x <= size]

    if larger:
        return "%sx%s" % (larger[0], larger[0])
    elif smaller:
        return "%sx%s" % (smaller[-1], smaller[-1])
    msg = (
        "Thumbnail size %s is not defined in settings "
        "and it won't be generated automatically" % size_name
    )
    warnings.warn(msg)
    return None


@register.simple_tag()
def get_thumbnail(image_file, size, method, rendition_key_set="products"):
    if image_file:
        used_size = get_thumbnail_size(size, method, rendition_key_set)
        try:
            thumbnail = getattr(image_file, method)[used_size]
        except Exception:
            logger.exception(
                "Thumbnail fetch failed", extra={"image_file": image_file, "size": size}
            )
        else:
            return thumbnail.url
    return static(choose_placeholder("%sx%s" % (size, size)))


@register.simple_tag()
def get_product_image_thumbnail(instance, size, method):
    image_file = instance.image if instance else None
    return get_thumbnail(image_file, size, method)


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


def validate_image_file(file, field_name):
    """Validate if the file is an image."""
    if not file:
        raise ValidationError({field_name: ValidationError("File is required", code="required")})
    if not file.content_type.startswith("image/"):
        raise ValidationError({field_name: ValidationError("Invalid file type", code="invalid")})
