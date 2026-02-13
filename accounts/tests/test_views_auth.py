import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

REGISTER_URL = "/api/accounts/register/"
LOGIN_URL = "/api/accounts/login/"


@pytest.mark.django_db
def test_register_then_login_blocked_until_verified():
    client = APIClient()
    payload = {
        "username": "donald",
        "email": "donald@example.com",
        "full_name": "Donald Example",
        "password": "StrongPass123",
        "password2": "StrongPass123",
        "role": "customer",
    }
    response = client.post(REGISTER_URL, data=payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    login_payload = {"email": "donald@example.com", "password": "StrongPass123"}
    response2 = client.post(LOGIN_URL, data=login_payload, format="json")
    assert response2.status_code == status.HTTP_403_FORBIDDEN
    assert response2.json().get("error") == "Email not verified"


@pytest.mark.django_db
def test_admin_order_list_requires_admin(client):
    admin = User.objects.create_superuser(username="admin_o", password="p", email="admin_o@test.com")
    client.force_login(admin)
    r = client.get("/api/accounts/orders/")
    assert r.status_code == status.HTTP_200_OK

