import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
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
    assert "access" not in r.json()
    assert "refresh" not in r.json()
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies


@pytest.mark.django_db
def test_login_with_unknown_username_fails(client):
    r = client.post("/api/accounts/login/", data={"username": "missing_user", "password": "StrongPass123"})
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_sets_http_only_cookies(client):
    user = User.objects.create_user(
        username="cookie_user",
        email="cookie@example.com",
        password="StrongPass123",
        full_name="Cookie User",
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    r = client.post("/api/accounts/login/", data={"email": user.email, "password": "StrongPass123"})
    assert r.status_code == status.HTTP_200_OK
    assert r.cookies["access_token"]["httponly"] is True
    assert r.cookies["refresh_token"]["httponly"] is True


@pytest.mark.django_db
def test_logout_clears_cookies(client):
    user = User.objects.create_user(
        username="logout_cookie",
        email="logout_cookie@example.com",
        password="StrongPass123",
        full_name="Logout Cookie",
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])

    login = client.post("/api/accounts/login/", data={"email": user.email, "password": "StrongPass123"})
    client.cookies["access_token"] = login.cookies["access_token"].value
    client.cookies["refresh_token"] = login.cookies["refresh_token"].value
    client.cookies["csrftoken"] = login.cookies["csrftoken"].value

    r = client.post("/api/accounts/logout/", HTTP_X_CSRFTOKEN=login.cookies["csrftoken"].value)
    assert r.status_code == status.HTTP_200_OK
    assert r.cookies["access_token"]["max-age"] == 0
    assert r.cookies["refresh_token"]["max-age"] == 0
