import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from menu.models import Category, MenuItem

User = get_user_model()

MENU_URL = "/api/menu/menu/"


@pytest.mark.django_db
def test_menu_viewset_public_list_and_retrieve(client):
    c = Category.objects.create(name="Rice", slug="rice")
    item = MenuItem.objects.create(category=c, name="Jollof", slug="jollof", price=1000, is_available=True)

    r_list = client.get(MENU_URL)
    assert r_list.status_code == status.HTTP_200_OK

    r_detail = client.get(f"{MENU_URL}{item.id}/")
    assert r_detail.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_menu_viewset_admin_crud(client):
    admin = User.objects.create_superuser(username="admin_menu", password="p", email="admin_menu@test.com")
    client.force_login(admin)

    c = Category.objects.create(name="Wraps", slug="wraps")
    payload = {
        "category": c.id,
        "name": "Veggie Wrap",
        "slug": "veggie-wrap",
        "description": "Healthy",
        "price": 1000,
        "is_available": True,
    }
    r_create = client.post(MENU_URL, data=payload)
    assert r_create.status_code in (200, 201)
    item_id = r_create.json().get("id") or r_create.json().get("data", {}).get("id")

    r_update = client.patch(f"{MENU_URL}{item_id}/", {"name": "Updated Wrap"})
    assert r_update.status_code in (200, 202)

    r_status = client.patch(f"{MENU_URL}{item_id}/update_status/", {"is_available": False})
    assert r_status.status_code == status.HTTP_200_OK

    r_delete = client.delete(f"{MENU_URL}{item_id}/")
    assert r_delete.status_code in (200, 204)
