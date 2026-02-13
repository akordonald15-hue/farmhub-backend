from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from cloudinary.models import CloudinaryField
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string

ROLE_CHOICES = (
    ("admin", "Admin"),
    ("farmer", "Farmer"),
    ("vendor", "Vendor"),
    ("logistics", "LogisticsAgent"),
    ("customer", "Customer"),
)


class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, role="customer", **extra_fields):
        if not email:
            username = extra_fields.get("username")
            if username:
                email = f"{username}@example.com"
                # Allow internal/test users created without an email to be treated as verified.
                extra_fields.setdefault("is_verified", True)
            else:
                raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email, password=password, role="admin", **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="customer")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email

    class Meta:
        ordering = ["-date_joined"]

    def natural_key(self):
        return (self.email,)


class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="verification")
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    last_otp_sent_at = models.DateTimeField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_otp(self):
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.otp_expires_at = timezone.now() + timedelta(minutes=10)
        self.otp_attempts = 0
        self.last_otp_sent_at = timezone.now()
        self.save()
        return self.otp

    def is_otp_expired(self):
        return not self.otp_expires_at or timezone.now() > self.otp_expires_at

    def increment_attempts(self):
        self.otp_attempts = (self.otp_attempts or 0) + 1
        self.save(update_fields=["otp_attempts"])
        return self.otp_attempts

    def invalidate_otp(self):
        self.otp = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.save(update_fields=["otp", "otp_expires_at", "otp_attempts"])

    def mark_verified(self):
        self.is_verified = True
        self.otp = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.save(update_fields=["is_verified", "otp", "otp_expires_at", "otp_attempts"])

        self.user.is_verified = True
        self.user.save(update_fields=["is_verified"])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_verified and not self.user.is_verified:
            self.user.is_verified = True
            self.user.save(update_fields=["is_verified"])

    def __str__(self):
        return f"EmailVerification({self.user.email})"

    class Meta:
        ordering = ["-generated_at"]


class BaseProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar = CloudinaryField("avatar", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomerProfile(BaseProfile):
    preferred_payment_method = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"CustomerProfile({self.user.email})"

    class Meta:
        ordering = ["-created_at"]


class FarmerProfile(BaseProfile):
    farm_name = models.CharField(max_length=255, blank=True, null=True)
    farm_location = models.CharField(max_length=255, blank=True, null=True)
    bvn = models.CharField(max_length=20, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"FarmerProfile({self.user.email})"

    class Meta:
        ordering = ["-created_at"]


class VendorProfile(BaseProfile):
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    shop_address = models.CharField(max_length=255, blank=True, null=True)
    rc_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"VendorProfile({self.user.email})"

    class Meta:
        ordering = ["-created_at"]


class LogisticsAgentProfile(BaseProfile):
    vehicle_number = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"LogisticsAgentProfile({self.user.email})"

    class Meta:
        ordering = ["-created_at"]
