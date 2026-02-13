import pytest
from django.core.cache import cache
from rest_framework import status
from django.contrib.auth import get_user_model
from menu.models import Category, MenuItem

PUBLIC_MENU_URL = "/api/menu/public/menu/"
ADMIN_ITEMS_URL = "/api/menu/admin/items/"

User = get_user_model()


@pytest.mark.django_db
def test_public_menu_cache_hit_uses_cached_payload(client):
    cached_payload = [{"id": 1, "name": "Cached Item"}]
    cache.set("public_menu_list_v1", cached_payload)

    r = client.get(PUBLIC_MENU_URL)
    assert r.status_code == status.HTTP_200_OK
    assert r.json().get("data") == cached_payload


@pytest.mark.django_db
def test_menu_cache_invalidated_on_admin_update(client):
    admin = User.objects.create_superuser(username="admin", password="p", email="admin@test.com")
    client.force_login(admin)

    category = Category.objects.create(name="Wraps", slug="wraps")
    item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap",
        slug="chicken-wrap",
        description="Tasty",
        price=1200,
        is_available=True,
    )

    client.get(PUBLIC_MENU_URL)
    assert cache.get("public_menu_list_v1") is not None

    r = client.patch(f"{ADMIN_ITEMS_URL}{item.id}/update_status/", {"is_available": False})
    assert r.status_code == status.HTTP_200_OK
    assert cache.get("public_menu_list_v1") is None


@pytest.mark.django_db
def test_non_admin_cannot_update_status(client):
    user = User.objects.create_user(username="user", password="p")
    client.force_login(user)

    category = Category.objects.create(name="Wraps", slug="wraps")
    item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap",
        slug="chicken-wrap",
        description="Tasty",
        price=1200,
        is_available=True,
    )

    r = client.patch(f"{ADMIN_ITEMS_URL}{item.id}/update_status/", {"is_available": False})
    assert r.status_code == status.HTTP_403_FORBIDDEN
