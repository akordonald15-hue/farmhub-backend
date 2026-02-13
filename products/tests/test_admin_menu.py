import pytest
from django.core.cache import cache
from rest_framework import status
from django.contrib.auth import get_user_model
from menu.models import Category, MenuItem

User = get_user_model()
ADMIN_ITEMS_URL = "/api/menu/admin/items/"

# Fixtures OUTSIDE the class
@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="p"
    )

@pytest.fixture
def regular_user():
    return User.objects.create_user(
        username="user",
        email="user@test.com",
        password="p"
    )

@pytest.fixture
def category():
    return Category.objects.create(name="Wraps", slug="wraps")

@pytest.fixture
def menu_item(category):
    return MenuItem.objects.create(
        category=category,
        name="Chicken Wrap",
        slug="chicken-wrap",
        description="Tasty",
        price=1200,
        is_available=True
    )

@pytest.mark.django_db
class TestAdminMenu:

    def test_admin_can_create_menu_item(self, client, admin_user, category):
        client.force_login(admin_user)
        payload = {
            "category": category.id,
            "name": "Veggie Wrap",
            "slug": "veggie-wrap",
            "description": "Healthy",
            "price": 1000,
            "is_available": True
        }
        cache.set("public_menu_list_v1", "cached_value")
        r = client.post(ADMIN_ITEMS_URL, data=payload)
        assert r.status_code in (201, 200)
        assert MenuItem.objects.filter(slug="veggie-wrap").exists()
        assert cache.get("public_menu_list_v1") is None

    def test_non_admin_cannot_create(self, client, regular_user, category):
        client.force_login(regular_user)
        payload = {
            "category": category.id,
            "name": "Unauthorized Wrap",
            "slug": "unauth-wrap",
            "description": "Should fail",
            "price": 900,
            "is_available": True
        }
        r = client.post(ADMIN_ITEMS_URL, data=payload)
        assert r.status_code == 403
        assert not MenuItem.objects.filter(slug="unauth-wrap").exists()

    def test_admin_can_update_menu_item(self, client, admin_user, menu_item):
        client.force_login(admin_user)
        url = f"{ADMIN_ITEMS_URL}{menu_item.id}/"
        r = client.patch(url, {"name": "Updated Wrap", "price": 1500})
        assert r.status_code in (200, 202)
        menu_item.refresh_from_db()
        assert menu_item.name == "Updated Wrap"

    def test_admin_can_delete_menu_item(self, client, admin_user, menu_item):
        client.force_login(admin_user)
        url = f"{ADMIN_ITEMS_URL}{menu_item.id}/"
        r = client.delete(url)
        assert r.status_code in (204, 200)
        assert not MenuItem.objects.filter(id=menu_item.id).exists()

    def test_admin_can_update_status(self, client, admin_user, menu_item):
        client.force_login(admin_user)
        url = f"{ADMIN_ITEMS_URL}{menu_item.id}/update_status/"
        r = client.patch(url, {"is_available": False})
        assert r.status_code == 200
        menu_item.refresh_from_db()
        assert menu_item.is_available is False
