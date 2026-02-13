import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import EmailVerification

User = get_user_model()

REGISTER_URL = "/api/accounts/register/"
VERIFY_URL = "/api/accounts/verify-email/"
RESEND_URL = "/api/accounts/resend-otp/"
LOGIN_URL = "/api/accounts/login/"
REFRESH_URL = "/api/accounts/refresh-token/"


@pytest.mark.django_db
def test_register_requires_full_name():
    client = APIClient()
    payload = {
        "username": "no_full",
        "email": "nofull@example.com",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "role": "customer",
    }
    r = client.post(REGISTER_URL, data=payload, format="json")
    assert r.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_register_username_cannot_have_spaces():
    client = APIClient()
    payload = {
        "username": "bad name",
        "email": "badname@example.com",
        "full_name": "Bad Name",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "role": "customer",
    }
    r = client.post(REGISTER_URL, data=payload, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in r.json()


@pytest.mark.django_db
def test_verify_email_already_verified():
    user = User.objects.create_user(email="verified@example.com", password="StrongPass123", full_name="V User")
    verification = EmailVerification.objects.get(user=user)
    verification.is_verified = True
    verification.save()

    client = APIClient()
    r = client.post(VERIFY_URL, data={"email": user.email, "otp": "000000"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("error") == "Email already verified."


@pytest.mark.django_db
def test_resend_otp_for_verified_user():
    user = User.objects.create_user(email="verified2@example.com", password="StrongPass123", full_name="V User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    verification = EmailVerification.objects.get(user=user)
    verification.is_verified = True
    verification.save(update_fields=["is_verified"])

    client = APIClient()
    r = client.post(RESEND_URL, data={"email": user.email}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("error") == "Email already verified."


@pytest.mark.django_db
def test_login_invalid_credentials():
    user = User.objects.create_user(email="login@example.com", password="StrongPass123", full_name="Login User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    client = APIClient()
    r = client.post(LOGIN_URL, data={"email": user.email, "password": "WrongPass123"}, format="json")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_requires_email_or_username():
    client = APIClient()
    r = client.post(LOGIN_URL, data={"password": "StrongPass123"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_with_username():
    user = User.objects.create_user(username="u_login", email="u_login@example.com", password="StrongPass123", full_name="User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    client = APIClient()
    r = client.post(LOGIN_URL, data={"username": "u_login", "password": "StrongPass123"}, format="json")
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_resend_otp_invalid_email():
    client = APIClient()
    r = client.post(RESEND_URL, data={"email": "missing@example.com"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_verify_email_invalid_user():
    client = APIClient()
    r = client.post(VERIFY_URL, data={"email": "missing@example.com", "otp": "123456"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_order_list_forbidden_for_non_admin(client):
    user = User.objects.create_user(email="basic@example.com", password="p", full_name="Basic")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)
    r = client.get("/api/accounts/orders/")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_refresh_token_invalid_returns_401(client):
    r = client.post(REFRESH_URL, data={"refresh_token": "bad"}, format="json")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_verified_token_obtain_pair_unverified():
    user = User.objects.create_user(email="pair@example.com", password="StrongPass123", full_name="Pair")
    client = APIClient()
    r = client.post("/api/accounts/token/", data={"email": user.email, "password": "StrongPass123"}, format="json")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_verified_token_refresh_blocks_unverified():
    user = User.objects.create_user(email="pair2@example.com", password="StrongPass123", full_name="Pair2")
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    r = client.post("/api/accounts/token/refresh/", data={"refresh": str(refresh)}, format="json")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_verified_token_refresh_success():
    user = User.objects.create_user(email="pair3@example.com", password="StrongPass123", full_name="Pair3")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    r = client.post("/api/accounts/token/refresh/", data={"refresh": str(refresh)}, format="json")
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_custom_refresh_token_success():
    user = User.objects.create_user(email="pair4@example.com", password="StrongPass123", full_name="Pair4")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    r = client.post(REFRESH_URL, data={"refresh_token": str(refresh)}, format="json")
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_logout_success(client):
    user = User.objects.create_user(email="logout@example.com", password="StrongPass123", full_name="Logout")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)
    r = client.post("/api/accounts/logout/")
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_refresh_token_rejected_for_unverified_user():
    user = User.objects.create_user(email="unverified@example.com", password="StrongPass123", full_name="Unverified")
    token = RefreshToken.for_user(user)
    client = APIClient()
    r = client.post(REFRESH_URL, data={"refresh_token": str(token)}, format="json")
    assert r.status_code == status.HTTP_403_FORBIDDEN
