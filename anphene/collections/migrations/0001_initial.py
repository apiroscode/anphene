# Generated by Django 3.0.6 on 2020-06-03 14:59

import core.utils.images
import django.contrib.postgres.fields.citext
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import versatileimagefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('is_published', models.BooleanField(default=False)),
                ('seo_title', models.CharField(blank=True, max_length=70, null=True, validators=[django.core.validators.MaxLengthValidator(70)])),
                ('seo_description', models.CharField(blank=True, max_length=300, null=True, validators=[django.core.validators.MaxLengthValidator(300)])),
                ('name', django.contrib.postgres.fields.citext.CICharField(max_length=250, unique=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('background_image', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to=core.utils.images.UploadToPathAndRename(field='name', path='collection-backgrounds'))),
                ('background_image_alt', models.CharField(blank=True, max_length=128)),
                ('description', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ('slug',),
                'permissions': (('manage_collections', 'Manage collections'),),
            },
        ),
        migrations.CreateModel(
            name='CollectionProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(db_index=True, editable=False, null=True)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collectionproduct', to='collections.Collection')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collectionproduct', to='products.Product')),
            ],
            options={
                'unique_together': {('collection', 'product')},
            },
        ),
        migrations.AddField(
            model_name='collection',
            name='products',
            field=models.ManyToManyField(blank=True, related_name='collections', through='collections.CollectionProduct', to='products.Product'),
        ),
    ]
