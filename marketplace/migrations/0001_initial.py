# Generated manually to ensure proper dependency ordering in tests.

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farmers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "Category",
                "verbose_name_plural": "Categories",
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(blank=True, db_index=True, max_length=300)),
                ("description", models.TextField(blank=True)),
                ("unit", models.CharField(default="kg", max_length=30)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("quantity", models.DecimalField(decimal_places=3, default=0, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.000"))])),
                ("min_order", models.DecimalField(decimal_places=3, default=1, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.001"))])),
                ("is_active", models.BooleanField(default=True)),
                ("featured", models.BooleanField(default=False)),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="marketplace.category")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_products", to=settings.AUTH_USER_MODEL)),
                ("farmer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="market_products", to="farmers.farmer")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
                "indexes": [
                    models.Index(fields=["farmer", "title"], name="marketplace_farmer_8dc13c_idx"),
                    models.Index(fields=["slug"], name="marketplace_slug_354b60_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("image_url", models.URLField(blank=True, help_text="Cloud URL for the image (Cloudinary/S3)")),
                ("alt_text", models.CharField(blank=True, max_length=255)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="marketplace.product")),
            ],
            options={
                "ordering": ["order", "-created_at"],
                "verbose_name": "Product Image",
                "verbose_name_plural": "Product Images",
            },
        ),
        migrations.CreateModel(
            name="InventoryRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("change_type", models.CharField(choices=[("IN", "IN"), ("OUT", "OUT"), ("ADJUST", "ADJUST"), ("RETURN", "RETURN")], max_length=10)),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.000"))])),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_actions", to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory_records", to="marketplace.product")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Inventory Record",
                "verbose_name_plural": "Inventory Records",
            },
        ),
    ]
