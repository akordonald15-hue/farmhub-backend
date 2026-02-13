import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
def test_admin_update_status_requires_status_field(client):
    admin = User.objects.create_superuser(username="admin2", password="p", email="admin2@test.com")
    user = User.objects.create_user(username="user2", password="p")
    client.force_login(admin)

    category = Category.objects.create(name="Wraps", slug="wraps")
    menu_item = MenuItem.objects.create(category=category, name="Wrap", slug="wrap", price=100)
    order = Order.objects.create(user=user, total_price=100)
    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=1, price=menu_item.price)

    r = client.patch(f"/api/orders/{order.id}/update_status/", {}, content_type="application/json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_paystack_webhook_missing_reference(client):
    r = client.post("/api/orders/paystack_webhook/", data={}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert r.json().get("error") == "Reference is required."
