import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.mark.django_db
def test_login_with_username_success(client):
    user = User.objects.create_user(
        username="user_one",
        email="user_one@example.com",
        password="StrongPass123",
        full_name="User One",
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    r = client.post("/api/accounts/login/", data={"username": "user_one", "password": "StrongPass123"})
    assert r.status_code == status.HTTP_200_OK
    assert "access" in r.json()


@pytest.mark.django_db
def test_login_with_unknown_username_fails(client):
    r = client.post("/api/accounts/login/", data={"username": "missing_user", "password": "StrongPass123"})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_verified_token_refresh_requires_verified_user(client):
    user = User.objects.create_user(
        username="unverified_user",
        email="unverified@example.com",
        password="StrongPass123",
        full_name="Unverified User",
    )
    refresh = RefreshToken.for_user(user)
    r = client.post("/api/accounts/token/refresh/", data={"refresh": str(refresh)})
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_verified_token_refresh_allows_verified_user(client):
    user = User.objects.create_user(
        username="verified_user",
        email="verified@example.com",
        password="StrongPass123",
        full_name="Verified User",
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    refresh = RefreshToken.for_user(user)
    r = client.post("/api/accounts/token/refresh/", data={"refresh": str(refresh)})
    assert r.status_code == status.HTTP_200_OK
    assert "access" in r.json()
