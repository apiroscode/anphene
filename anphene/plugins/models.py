from django.contrib.postgres.fields import JSONField
from django.db import models

from ..core.permissions import PluginsPermissions


class PluginConfiguration(models.Model):
    identifier = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=False)
    type = models.CharField(max_length=128, blank=True)
    configuration = JSONField(blank=True, null=True, default=dict)

    class Meta:
        permissions = ((PluginsPermissions.MANAGE_PLUGINS.codename, "Manage plugins"),)

    def __str__(self):
        return f"Configuration of {self.name}, active: {self.active}"
