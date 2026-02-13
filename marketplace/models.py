# marketplace/models.py
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Global product listing — links to farmer (vendor) via farmers.Farmer.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey("farmers.Farmer", on_delete=models.CASCADE, related_name="market_products")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, blank=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=30, default='kg')
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0, validators=[MinValueValidator(Decimal('0.000'))])
    min_order = models.DecimalField(max_digits=12, decimal_places=3, default=1, validators=[MinValueValidator(Decimal('0.001'))])
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    metadata = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['farmer', 'title']),
            models.Index(fields=['slug']),
        ]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.title} — {self.farmer}"

    def adjust_quantity(self, delta):
        """
        Convenience wrapper. Use services.adjust_product_stock for atomic operations.
        """
        self.quantity = self.quantity + Decimal(delta)
        self.save(update_fields=['quantity', 'updated_at'])


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(blank=True, help_text="Cloud URL for the image (Cloudinary/S3)")
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product} ({self.id})"


class InventoryRecord(models.Model):
    """
    Historical log of stock changes for auditing and reports.
    """
    CHANGE_TYPES = [
        ('IN', 'IN'),
        ('OUT', 'OUT'),
        ('ADJUST', 'ADJUST'),
        ('RETURN', 'RETURN'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_records')
    change_type = models.CharField(max_length=10, choices=CHANGE_TYPES)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, validators=[MinValueValidator(Decimal('0.000'))])
    note = models.TextField(blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_actions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Inventory Record"
        verbose_name_plural = "Inventory Records"

    def __str__(self):
        return f"{self.product} {self.change_type} {self.quantity}"
