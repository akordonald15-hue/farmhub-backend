import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory

from menu.models import Category, MenuItem
from orders.models import Order, OrderItem
from orders.views import IsOwnerOrAdmin

User = get_user_model()


@pytest.mark.django_db
def test_order_create_endpoint(client):
    user = User.objects.create_user(username="order_create_user", password="p")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    category = Category.objects.create(name="Wraps3", slug="wraps3")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 3",
        slug="chicken-wrap-3",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    payload = {"items": [{"menu_item": menu_item.id, "quantity": 1}]}
    resp = client.post("/api/orders/create/", payload, content_type="application/json")
    assert resp.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_order_list_query_count_stable(client, django_assert_num_queries):
    user = User.objects.create_user(username="order_list_user", password="p")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    category = Category.objects.create(name="Wraps4", slug="wraps4")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 4",
        slug="chicken-wrap-4",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    order = Order.objects.create(user=user, total_price=1200)
    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=1, price=menu_item.price)

    with django_assert_num_queries(6):
        resp = client.get("/api/orders/")
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_is_owner_or_admin_permission():
    user = User.objects.create_user(username="order_owner", password="p")
    other = User.objects.create_user(username="order_other", password="p")
    order = Order.objects.create(user=user, total_price=10)

    factory = APIRequestFactory()
    request = factory.get("/api/orders/")
    request.user = user
    assert IsOwnerOrAdmin().has_object_permission(request, None, order) is True

    request.user = other
    assert IsOwnerOrAdmin().has_object_permission(request, None, order) is False
