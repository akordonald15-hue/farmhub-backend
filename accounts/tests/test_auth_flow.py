import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import EmailVerification

User = get_user_model()

REGISTER_URL = "/api/accounts/register/"
VERIFY_URL = "/api/accounts/verify-email/"
RESEND_URL = "/api/accounts/resend-otp/"
LOGIN_URL = "/api/accounts/login/"
ME_URL = "/api/accounts/me/"
ORDERS_URL = "/api/orders/"


def register_user(client, email="user@example.com", username="user1"):
    payload = {
        "username": username,
        "email": email,
        "full_name": "Test User",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "role": "customer",
    }
    response = client.post(REGISTER_URL, data=payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    return User.objects.get(email=email)


@pytest.mark.django_db
def test_registration_creates_unverified_user():
    client = APIClient()
    user = register_user(client)
    user.refresh_from_db()

    verification = EmailVerification.objects.get(user=user)
    assert user.is_verified is False
    assert verification.is_verified is False
    assert verification.otp is not None
    assert verification.otp_expires_at is not None
    assert verification.otp_expires_at > timezone.now()


@pytest.mark.django_db
def test_login_blocked_for_unverified_user():
    client = APIClient()
    register_user(client)

    response = client.post(
        LOGIN_URL,
        data={"email": "user@example.com", "password": "StrongPass123"},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json().get("error") == "Email not verified"


@pytest.mark.django_db
def test_otp_verification_marks_user_verified():
    client = APIClient()
    user = register_user(client)
    verification = EmailVerification.objects.get(user=user)

    response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": verification.otp},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("message") == "Email verified successfully"

    user.refresh_from_db()
    verification.refresh_from_db()
    assert user.is_verified is True
    assert verification.is_verified is True
    assert verification.otp is None


@pytest.mark.django_db
def test_otp_expiry_enforced():
    client = APIClient()
    user = register_user(client, email="expired@example.com", username="expired")
    verification = EmailVerification.objects.get(user=user)

    verification.otp = "123456"
    verification.otp_expires_at = timezone.now() - timedelta(minutes=1)
    verification.save(update_fields=["otp", "otp_expires_at"])

    response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": "123456"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "OTP expired. Please request a new OTP."

    verification.refresh_from_db()
    assert verification.otp is None
    assert verification.otp_expires_at is None


@pytest.mark.django_db
def test_otp_cannot_be_reused():
    client = APIClient()
    user = register_user(client, email="reuse@example.com", username="reuse")
    verification = EmailVerification.objects.get(user=user)
    otp = verification.otp

    response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": otp},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    response2 = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": otp},
        format="json",
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert response2.json().get("error") == "Email already verified."


@pytest.mark.django_db
def test_invalid_otp_increments_attempts():
    client = APIClient()
    user = register_user(client, email="invalid@example.com", username="invalid")
    verification = EmailVerification.objects.get(user=user)
    verification.otp = "123456"
    verification.otp_expires_at = timezone.now() + timedelta(minutes=5)
    verification.save(update_fields=["otp", "otp_expires_at"])

    response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": "000000"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "Invalid OTP."

    verification.refresh_from_db()
    assert verification.otp_attempts == 1


@pytest.mark.django_db
def test_otp_lockout_after_max_attempts():
    client = APIClient()
    user = register_user(client, email="lockout@example.com", username="lockout")
    verification = EmailVerification.objects.get(user=user)
    verification.otp = "123456"
    verification.otp_expires_at = timezone.now() + timedelta(minutes=5)
    verification.otp_attempts = 4
    verification.save(update_fields=["otp", "otp_expires_at", "otp_attempts"])

    response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": "000000"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("error") == "OTP invalidated. Please request a new OTP."

    verification.refresh_from_db()
    assert verification.otp is None
    assert verification.otp_attempts == 0


@pytest.mark.django_db
def test_resend_otp_rate_limited():
    client = APIClient()
    user = register_user(client, email="resend@example.com", username="resend")
    cache.clear()

    for _ in range(3):
        response = client.post(RESEND_URL, data={"email": user.email}, format="json")
        assert response.status_code == status.HTTP_200_OK

    response = client.post(RESEND_URL, data={"email": user.email}, format="json")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_verified_user_can_login_and_access_protected_endpoints():
    client = APIClient()
    user = register_user(client, email="verified@example.com", username="verified")
    verification = EmailVerification.objects.get(user=user)

    verify_response = client.post(
        VERIFY_URL,
        data={"email": user.email, "otp": verification.otp},
        format="json",
    )
    assert verify_response.status_code == status.HTTP_200_OK

    login_response = client.post(
        LOGIN_URL,
        data={"email": user.email, "password": "StrongPass123"},
        format="json",
    )
    assert login_response.status_code == status.HTTP_200_OK
    access = login_response.json().get("access")
    assert access

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    me_response = client.get(ME_URL)
    assert me_response.status_code == status.HTTP_200_OK

    orders_response = client.get(ORDERS_URL)
    assert orders_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_permissions_unauthenticated_and_unverified():
    client = APIClient()

    response = client.get(ME_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    user = register_user(client, email="blocked@example.com", username="blocked")
    client.force_authenticate(user=user)

    response2 = client.get(ME_URL)
    assert response2.status_code == status.HTTP_403_FORBIDDEN
