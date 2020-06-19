# Generated by Django 3.0.6 on 2020-06-03 14:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignedProductAttribute",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AssignedVariantAttribute",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Attribute",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=250, unique=True)),
                (
                    "input_type",
                    models.CharField(
                        choices=[("dropdown", "Dropdown"), ("multiselect", "Multi Select")],
                        default="dropdown",
                        max_length=50,
                    ),
                ),
                ("value_required", models.BooleanField(blank=True, default=False)),
                ("visible_in_storefront", models.BooleanField(blank=True, default=True)),
                ("filterable_in_storefront", models.BooleanField(blank=True, default=True)),
                ("filterable_in_dashboard", models.BooleanField(blank=True, default=True)),
                ("storefront_search_position", models.IntegerField(blank=True, default=0)),
                ("available_in_grid", models.BooleanField(blank=True, default=True)),
            ],
            options={
                "ordering": ("storefront_search_position", "slug"),
                "permissions": (("manage_attributes", "Manage attributes"),),
            },
        ),
        migrations.CreateModel(
            name="AttributeVariant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sort_order", models.IntegerField(db_index=True, editable=False, null=True)),
                (
                    "assigned_variants",
                    models.ManyToManyField(
                        blank=True,
                        related_name="attributesrelated",
                        through="attributes.AssignedVariantAttribute",
                        to="products.ProductVariant",
                    ),
                ),
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributevariant",
                        to="attributes.Attribute",
                    ),
                ),
                (
                    "product_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributevariant",
                        to="products.ProductType",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order",),
                "unique_together": {("attribute", "product_type")},
            },
        ),
        migrations.CreateModel(
            name="AttributeValue",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sort_order", models.IntegerField(db_index=True, editable=False, null=True)),
                ("name", models.CharField(max_length=250)),
                ("value", models.CharField(blank=True, default="", max_length=100)),
                ("slug", models.SlugField(max_length=255)),
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="values",
                        to="attributes.Attribute",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order", "id"),
                "unique_together": {("slug", "attribute")},
            },
        ),
        migrations.CreateModel(
            name="AttributeProduct",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sort_order", models.IntegerField(db_index=True, editable=False, null=True)),
                (
                    "assigned_products",
                    models.ManyToManyField(
                        blank=True,
                        related_name="attributesrelated",
                        through="attributes.AssignedProductAttribute",
                        to="products.Product",
                    ),
                ),
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributeproduct",
                        to="attributes.Attribute",
                    ),
                ),
                (
                    "product_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attributeproduct",
                        to="products.ProductType",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order",),
                "unique_together": {("attribute", "product_type")},
            },
        ),
        migrations.AddField(
            model_name="attribute",
            name="product_types",
            field=models.ManyToManyField(
                blank=True,
                related_name="product_attributes",
                through="attributes.AttributeProduct",
                to="products.ProductType",
            ),
        ),
        migrations.AddField(
            model_name="attribute",
            name="product_variant_types",
            field=models.ManyToManyField(
                blank=True,
                related_name="variant_attributes",
                through="attributes.AttributeVariant",
                to="products.ProductType",
            ),
        ),
        migrations.AddField(
            model_name="assignedvariantattribute",
            name="assignment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="variantassignments",
                to="attributes.AttributeVariant",
            ),
        ),
        migrations.AddField(
            model_name="assignedvariantattribute",
            name="value",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="attributes.AttributeValue"
            ),
        ),
        migrations.AddField(
            model_name="assignedvariantattribute",
            name="variant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="products.ProductVariant",
            ),
        ),
        migrations.AddField(
            model_name="assignedproductattribute",
            name="assignment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="productassignments",
                to="attributes.AttributeProduct",
            ),
        ),
        migrations.AddField(
            model_name="assignedproductattribute",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="products.Product",
            ),
        ),
        migrations.AddField(
            model_name="assignedproductattribute",
            name="values",
            field=models.ManyToManyField(to="attributes.AttributeValue"),
        ),
        migrations.AlterUniqueTogether(
            name="assignedvariantattribute", unique_together={("variant", "assignment")},
        ),
        migrations.AlterUniqueTogether(
            name="assignedproductattribute", unique_together={("product", "assignment")},
        ),
    ]