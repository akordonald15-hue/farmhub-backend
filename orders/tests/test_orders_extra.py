import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
def test_admin_update_status_requires_status_field(client):
    admin = User.objects.create_superuser(username="admin_status", password="p", email="admin_status@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    user = User.objects.create_user(username="user_status", password="p")

    category = Category.objects.create(name="Wraps2", slug="wraps2")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap",
        slug="chicken-wrap-2",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    order = Order.objects.create(user=user, total_price=1200)
    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=1, price=menu_item.price)

    client.force_login(admin)
    url = f"/api/orders/{order.id}/update_status/"
    resp = client.patch(url, {}, content_type="application/json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_paystack_webhook_missing_reference(client):
    resp = client.post("/api/orders/paystack_webhook/", data={}, content_type="application/json")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_paystack_webhook_reference_not_found(client):
    resp = client.post("/api/orders/paystack_webhook/", data={"reference": "missing-ref"}, content_type="application/json")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
