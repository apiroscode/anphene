# Generated by Django 3.0.6 on 2020-06-02 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='note',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
