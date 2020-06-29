# Generated by Django 3.0.6 on 2020-06-19 21:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("menus", "0001_initial"),
        ("collections", "0002_auto_20200611_1629"),
        ("site", "0003_patch_site"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="bottom_menu",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="menus.Menu",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="homepage_collection",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="collections.Collection",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="top_menu",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="menus.Menu",
            ),
        ),
    ]