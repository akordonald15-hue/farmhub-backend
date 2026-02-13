import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import UserSerializer, RegistrationSerializer, ResendOTPSerializer

User = get_user_model()


@pytest.mark.django_db
def test_user_serializer_profile_none_for_unknown_role():
    user = User.objects.create_user(email="unknown_role@example.com", password="StrongPass123", full_name="Unknown")
    user.role = "unknown"
    user.save(update_fields=["role"])
    data = UserSerializer(user).data
    assert data["profile"] is None


def test_user_serializer_profile_handles_bad_manager():
    class DummyManager:
        def first(self):
            raise Exception("bad manager")

    class DummyUser:
        role = "customer"
        customerprofile = DummyManager()

    serializer = UserSerializer()
    assert serializer.get_profile(DummyUser()) is None


@pytest.mark.django_db
def test_registration_serializer_duplicate_email_and_missing_fields():
    User.objects.create_user(email="dup@example.com", password="StrongPass123", full_name="Dup User")

    serializer = RegistrationSerializer(data={
        "email": "dup@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "full_name": "Dup User",
        "username": "dup_user",
        "role": "customer",
    })
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)

    serializer_missing = RegistrationSerializer(data={
        "email": "missing@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "full_name": "",
        "username": "",
        "role": "customer",
    })
    with pytest.raises(serializers.ValidationError):
        serializer_missing.is_valid(raise_exception=True)


def test_resend_otp_serializer_validates_otp():
    serializer = ResendOTPSerializer()
    with pytest.raises(serializers.ValidationError):
        serializer.validate_otp("12ab56")

    with pytest.raises(serializers.ValidationError):
        serializer.validate_otp("12345")
