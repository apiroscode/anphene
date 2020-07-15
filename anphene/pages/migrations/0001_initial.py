# Generated by Django 3.0.6 on 2020-07-14 06:02

import django.core.validators
import draftjs_sanitizer
from django.db import migrations, models

import core.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("publication_date", models.DateField(blank=True, null=True)),
                ("is_published", models.BooleanField(default=False)),
                (
                    "seo_title",
                    models.CharField(
                        blank=True,
                        max_length=70,
                        validators=[django.core.validators.MaxLengthValidator(70)],
                    ),
                ),
                (
                    "seo_description",
                    models.CharField(
                        blank=True,
                        max_length=300,
                        validators=[django.core.validators.MaxLengthValidator(300)],
                    ),
                ),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("title", models.CharField(max_length=250)),
                (
                    "content",
                    core.db.fields.SanitizedJSONField(
                        blank=True, default=dict, sanitizer=draftjs_sanitizer.clean_draft_js
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("slug",), "permissions": (("manage_pages", "Manage pages."),),},
        ),
    ]
