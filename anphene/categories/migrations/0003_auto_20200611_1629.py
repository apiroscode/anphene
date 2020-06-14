# Generated by Django 3.0.6 on 2020-06-11 09:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0002_auto_20200611_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='seo_description',
            field=models.CharField(blank=True, default='', max_length=300, validators=[django.core.validators.MaxLengthValidator(300)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='seo_title',
            field=models.CharField(blank=True, default='', max_length=70, validators=[django.core.validators.MaxLengthValidator(70)]),
            preserve_default=False,
        ),
    ]
