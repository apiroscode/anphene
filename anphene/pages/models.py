from django.db import models
from draftjs_sanitizer import clean_draft_js

from core.db.fields import SanitizedJSONField
from core.db.models import PublishableModel, SeoModel
from ..core.permissions import PagePermissions


class Page(SeoModel, PublishableModel):
    slug = models.SlugField(unique=True, max_length=255)
    title = models.CharField(max_length=250)
    content = models.TextField(blank=True)
    content_json = SanitizedJSONField(blank=True, default=dict, sanitizer=clean_draft_js)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("slug",)
        permissions = ((PagePermissions.MANAGE_PAGES.codename, "Manage pages."),)

    def __str__(self):
        return self.title
