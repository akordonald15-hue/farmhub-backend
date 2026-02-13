# logistics/models.py
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

VEHICLE_TYPE_CHOICES = [
    ("MOTORCYCLE", "Motorcycle"),
    ("VAN", "Van"),
    ("TRUCK", "Truck"),
    ("Keke", "Keke"),
    ("OTHER", "Other"),
]

DISPATCH_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("ASSIGNED", "Assigned"),
    ("PICKED_UP", "Picked Up"),
    ("IN_TRANSIT", "In Transit"),
    ("DELIVERED", "Delivered"),
    ("FAILED", "Failed"),
    ("RETURNED", "Returned"),
]


class LogisticsAgent(models.Model):
    """
    A user who performs pickups and deliveries.
    This links to the project user model (optional).
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,  null=True, blank=True, related_name="logistics_agent_profile"
        )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Logistics Agent"
        verbose_name_plural = "Logistics Agents"

    def __str__(self):
        return f"{self.full_name}"


class Vehicle(models.Model):
    """
    Vehicles used for deliveries.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default="MOTORCYCLE")
    registration_number = models.CharField(max_length=100, unique=True)
    driver = models.ForeignKey(LogisticsAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles")
    capacity_description = models.CharField(max_length=255, blank=True, help_text="e.g. 100kg or 2 crates")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"

    def __str__(self):
        return f"{self.registration_number} ({self.vehicle_type})"


class Dispatch(models.Model):
    """
    A dispatch record created for either an order or a supply record.
    We reference orders.Order and farmers.SupplyRecord by string to avoid import-time issues.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    # Optional links: either order or supply_record can be set (or neither for manual dispatch)
    order = models.ForeignKey("orders.Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="dispatches")
    supply_record = models.ForeignKey("farmers.SupplyRecord", on_delete=models.SET_NULL, null=True, blank=True, related_name="dispatches")
    reference_code = models.CharField(max_length=120, blank=True, help_text="Optional external reference or tracking code")
    pickup_address = models.TextField(blank=True)
    dropoff_address = models.TextField(blank=True)
    assigned_agent = models.ForeignKey(LogisticsAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    assigned_vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="dispatches")
    status = models.CharField(max_length=20, choices=DISPATCH_STATUS_CHOICES, default="PENDING")
    estimated_pickup_time = models.DateTimeField(null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    pickup_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    proof_of_delivery_url = models.URLField(blank=True, help_text="Photo or signature URL")
    receiver_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_dispatches")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional delivery cost")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Dispatch"
        verbose_name_plural = "Dispatches"

    def __str__(self):
        return f"Dispatch {self.reference_code or self.id} - {self.status}"


class DispatchStatusUpdate(models.Model):
    """
    Timeline of status updates for a dispatch - useful for tracking history.
    """
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE, related_name="status_updates")
    status = models.CharField(max_length=20, choices=DISPATCH_STATUS_CHOICES)
    note = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Optional geo/location text")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Dispatch Status Update"
        verbose_name_plural = "Dispatch Status Updates"

    def __str__(self):
        return f"{self.dispatch} -> {self.status} @ {self.created_at}"
