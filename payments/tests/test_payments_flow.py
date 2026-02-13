import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from menu.models import Category, MenuItem
from orders.models import Order, OrderItem

User = get_user_model()

INIT_URL = "/api/payments/initialize/"
VERIFY_URL = "/api/payments/verify/"
WEBHOOK_URL = "/api/payments/webhook/"


@pytest.mark.django_db
def test_initialize_payment_order_not_found(client):
    user = User.objects.create_user(email="pay@example.com", password="StrongPass123", full_name="Pay User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    r = client.post(INIT_URL, data={"order_id": 9999}, format="json")
    assert r.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_verify_payment_not_successful(monkeypatch, client):
    user = User.objects.create_user(email="pay2@example.com", password="StrongPass123", full_name="Pay User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    category = Category.objects.create(name="Wraps", slug="wraps")
    item = MenuItem.objects.create(category=category, name="Wrap", slug="wrap", price=100)
    order = Order.objects.create(user=user, total_price=100)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, price=item.price)

    class DummyResp:
        status_code = 200
        def json(self):
            return {"data": {"status": "failed", "metadata": {"order_id": order.id}}}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResp())

    r = client.post(VERIFY_URL, data={"reference": "ref123"}, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_paystack_webhook_invalid_signature(client):
    payload = {"event": "charge.success", "data": {"reference": "ref", "metadata": {"order_id": 1}}}
    r = client.post(WEBHOOK_URL, data=payload, format="json", HTTP_X_PAYSTACK_SIGNATURE="invalid")
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_paystack_webhook_missing_signature(client):
    payload = {"event": "charge.success", "data": {"reference": "ref", "metadata": {"order_id": 1}}}
    r = client.post(WEBHOOK_URL, data=payload, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_verify_payment_success(monkeypatch, client):
    user = User.objects.create_user(email="pay3@example.com", password="StrongPass123", full_name="Pay User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    category = Category.objects.create(name="Wraps2", slug="wraps2")
    item = MenuItem.objects.create(category=category, name="Wrap2", slug="wrap2", price=100)
    order = Order.objects.create(user=user, total_price=100)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, price=item.price)

    class DummyResp:
        status_code = 200
        def json(self):
            return {"data": {"status": "success", "metadata": {"order_id": order.id}}}

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: DummyResp())
    r = client.post(VERIFY_URL, data={"reference": "ref123"}, format="json")
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_initialize_payment_success(monkeypatch, client):
    user = User.objects.create_user(email="pay_init@example.com", password="StrongPass123", full_name="Pay Init")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    category = Category.objects.create(name="Wraps3", slug="wraps3")
    item = MenuItem.objects.create(category=category, name="Wrap3", slug="wrap3", price=100)
    order = Order.objects.create(user=user, total_price=100)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, price=item.price)

    class DummyResp:
        status_code = 200
        def json(self):
            return {"data": {"reference": "ref-init"}}

    monkeypatch.setattr("requests.post", lambda *args, **kwargs: DummyResp())
    r = client.post(INIT_URL, data={"order_id": order.id}, format="json")
    assert r.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.paystack_reference == "ref-init"
