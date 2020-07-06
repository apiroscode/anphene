# Generated by Django 3.0.6 on 2020-07-04 06:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("site", "0005_auto_20200704_1138"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthorizationKey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("facebook", "Facebook-Oauth2"),
                            ("google-oauth2", "Google-Oauth2"),
                        ],
                        max_length=20,
                    ),
                ),
                ("key", models.TextField()),
                ("password", models.TextField()),
                (
                    "site_settings",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="site.SiteSettings"
                    ),
                ),
            ],
            options={"unique_together": {("site_settings", "name")},},
        ),
    ]
