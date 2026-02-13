import pytest
from accounts.serializers import RegistrationSerializer, LoginSerializer, UserSerializer
from accounts.models import CustomerProfile
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_registration_password_mismatch():
    serializer = RegistrationSerializer(
        data={
            "email": "a@example.com",
            "username": "usera",
            "full_name": "User A",
            "password": "StrongPass123",
            "password2": "Mismatch123",
            "role": "customer",
        }
    )
    assert serializer.is_valid() is False
    assert "password" in serializer.errors


def test_login_serializer_normalizes_email():
    serializer = LoginSerializer(data={"email": "TEST@EXAMPLE.COM", "password": "StrongPass123"})
    assert serializer.is_valid() is True
    assert serializer.validated_data["email"] == "test@example.com"


@pytest.mark.django_db
def test_user_serializer_includes_profile():
    user = User.objects.create_user(email="cust@example.com", password="p", full_name="Cust", role="customer")
    profile = CustomerProfile.objects.get(user=user)
    profile.phone = "123"
    profile.save()
    data = UserSerializer(user).data
    assert data["profile"] is not None
