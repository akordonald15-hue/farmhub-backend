# farmers/models.py
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

# Choices
FARM_TYPE_CHOICES = [
    ("CROPS", "Crops"),
    ("LIVESTOCK", "Livestock"),
    ("POULTRY", "Poultry"),
    ("AQUACULTURE", "Aquaculture"),
    ("MIXED", "Mixed"),
    ("OTHER", "Other"),
]

VERIFICATION_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("VERIFIED", "Verified"),
    ("REJECTED", "Rejected"),
]

UNIT_CHOICES = [
    ("kg", "Kilogram"),
    ("bag", "Bag"),
    ("crate", "Crate"),
    ("litre", "Litre"),
    ("piece", "Piece"),
    ("bird", "Bird"),
    ("ton", "Ton"),
    ("other", "Other"),
]


class Farmer(models.Model):
    """
    Farmer profile. Can be linked to a User account (if farmer signs up).
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="farmer_profile",
        help_text="Optional link to a User account"
    )
    business_name = models.CharField(max_length=255, blank=True, help_text="Optional farm or business name")
    contact_name = models.CharField(max_length=255, help_text="Farmer's full name")
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    farm_type = models.CharField(max_length=20, choices=FARM_TYPE_CHOICES, default="CROPS")
    farm_size = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Size (in hectares or specify unit in notes)")
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    state = models.CharField(max_length=100, blank=True)
    lga = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    profile_image = models.URLField(blank=True, null=True, help_text="Cloud URL for profile image")
    verified = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default="PENDING")
    verification_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(blank=True, null=True, help_text="Optional free-form metadata")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Farmer"
        verbose_name_plural = "Farmers"

    def __str__(self):
        if self.business_name:
            return f"{self.business_name} ({self.contact_name})"
        return f"{self.contact_name}"


class FarmerDocument(models.Model):
    """
    Documents uploaded for KYC / verification (NIN, business license, certificate).
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255, help_text="Document type or name")
    file_url = models.URLField(help_text="Cloud storage URL")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Farmer Document"
        verbose_name_plural = "Farmer Documents"

    def __str__(self):
        return f"{self.name} - {self.farmer}"


class FarmerProduct(models.Model):
    """
    Product listing created by a farmer — not the global Product catalog (that may live in products app).
    This model helps track vendor-specific stock, price and availability.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=255, help_text="Product name (e.g., Maize, Eggs)")
    category = models.CharField(max_length=150, blank=True, help_text="Optional product category")
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="kg")
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity_available = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)], default=0)
    min_order_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    harvest_date = models.DateField(null=True, blank=True, help_text="Optional harvest/packaging date")
    is_active = models.BooleanField(default=True)
    images = models.JSONField(null=True, blank=True, help_text="List of image URLs")
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Farmer Product"
        verbose_name_plural = "Farmer Products"
        indexes = [
            models.Index(fields=["farmer", "title"]),
        ]

    def __str__(self):
        return f"{self.title} — {self.farmer}"

    def reserve(self, qty):
        """
        Decrease available quantity by qty (atomic operations should be done at service layer).
        Returns True if successful, False if insufficient stock.
        """
        if qty <= 0:
            return False
        if self.quantity_available >= qty:
            self.quantity_available = models.F('quantity_available') - qty
            self.save(update_fields=["quantity_available"])
            return True
        return False


class SupplyRecord(models.Model):
    """
    Historical record of actual supplies / deliveries from farmer to the marketplace.
    Use this to track inbound stock, quality checks, and reconciliations.
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("COMPLETED", "Completed"),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name="supply_records")
    product = models.ForeignKey(FarmerProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name="supply_records")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="kg")
    supply_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    quality_notes = models.TextField(blank=True)
    received_by = models.CharField(max_length=255, blank=True, help_text="Name of the receiver at pickup/warehouse")
    reference_code = models.CharField(max_length=120, blank=True, help_text="Optional external reference")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-supply_date"]
        verbose_name = "Supply Record"
        verbose_name_plural = "Supply Records"
        indexes = [
            models.Index(fields=["farmer", "product", "status"]),
        ]

    def __str__(self):
        return f"{self.farmer} — {self.quantity} {self.unit} ({self.status})"
