from rest_framework import serializers
from django.contrib.auth import get_user_model
import bleach

from .models import (
    CustomerProfile,
    FarmerProfile,
    VendorProfile,
    LogisticsAgentProfile,
)

User = get_user_model()

# Define role choices at module level to avoid import-time User._meta access
ROLE_CHOICES = ("customer", "farmer", "vendor", "logistics")

# Bleach allowed tags and attributes (minimal for safety)
ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        exclude = ("id", "user")


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        exclude = ("id", "user")


class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        exclude = ("id", "user")


class LogisticsAgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticsAgentProfile
        exclude = ("id", "user")


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "username", "role", "is_verified", "profile")

    def get_profile(self, obj):
        """Fetch and serialize the user's role-specific profile."""
        role = getattr(obj, "role", None)
        
        # Map roles to their profile models and serializers
        mapping = {
            "customer": ("customerprofile", CustomerProfileSerializer),
            "farmer": ("farmerprofile", FarmerProfileSerializer),
            "vendor": ("vendorprofile", VendorProfileSerializer),
            "logistics": ("logisticsagentprofile", LogisticsAgentProfileSerializer),
        }
        
        item = mapping.get(role)
        if not item:
            return None
        
        attr_name, serializer_class = item
        profile = getattr(obj, attr_name, None)
        
        # Handle accidental related-manager (if present)
        try:
            if profile is not None and hasattr(profile, "first"):
                profile = profile.first()
        except Exception:
            profile = None
        
        return serializer_class(profile).data if profile else None


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default="customer")

    class Meta:
        model = User
        fields = ("email", "password", "password2", "full_name", "username", "role")

    def validate_email(self, value):
        """Validate and sanitize email."""
        value = value.lower().strip()
        # Bleach strip tags from email (shouldn't have any, but defensive)
        value = bleach.clean(value, tags=[], strip=True)
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_full_name(self, value):
        """Validate and sanitize full_name."""
        if not value:
            raise serializers.ValidationError("Full name is required.")
        # Strip HTML tags from full_name
        value = bleach.clean(value, tags=[], strip=True)
        return value.strip()

    def validate_username(self, value):
        """Validate and sanitize username."""
        if not value:
            raise serializers.ValidationError("Username is required.")
        if " " in value:
            raise serializers.ValidationError("Username cannot contain spaces.")
        # Strip HTML tags from username
        value = bleach.clean(value, tags=[], strip=True)
        return value.strip()

    def validate(self, attrs):
        """Validate password confirmation."""
        password = attrs.get("password")
        password2 = attrs.get("password2")
        
        if password != password2:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        return attrs

    def create(self, validated_data):
        """Create user and associated profile via signals."""
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        
        # Sanitize email and username
        validated_data["email"] = validated_data.get("email", "").lower().strip()
        validated_data["username"] = validated_data.get("username", "").strip()
        
        user = User.objects.create_user(password=password, **validated_data)
        # Signal handlers will create EmailVerification and role-specific profile
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate_email(self, value):
        """Sanitize and validate email."""
        value = value.lower().strip()
        value = bleach.clean(value, tags=[], strip=True)
        return value


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        value = bleach.clean(value, tags=[], strip=True)
        return value

    def validate_otp(self, value):
        """Validate OTP is numeric."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        if len(value) != 6:
            raise serializers.ValidationError("OTP must be 6 digits.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        """Sanitize and normalize email."""
        value = value.lower().strip()
        value = bleach.clean(value, tags=[], strip=True)
        return value

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")
        if not email and not username:
            raise serializers.ValidationError("Email or username is required.")
        if username:
            attrs["username"] = bleach.clean(username, tags=[], strip=True).strip()
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    pass
# ...existing code...
