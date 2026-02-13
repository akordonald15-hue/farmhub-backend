import pytest
from rest_framework import serializers
from orders.serializers import OrderSerializer
from products.models import Category, MenuItem
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_order_serializer_validations():
    user = User.objects.create_user(username="u_order", password="p")
    category = Category.objects.create(name="Wraps", slug="wraps")
    item = MenuItem.objects.create(category=category, name="Wrap", slug="wrap", price=10, is_available=True)

    serializer = OrderSerializer(
        data={"items": [], "address": "1234", "phone": "123"},
        context={"request": type("Req", (), {"user": user})()},
    )
    assert serializer.is_valid() is False

    serializer2 = OrderSerializer(
        data={"items": [{"menu_item": item.id, "quantity": 1}], "address": "12345", "phone": "12345678"},
        context={"request": type("Req", (), {"user": user})()},
    )
    assert serializer2.is_valid() is True
    order = serializer2.save()
    assert order.total_price == item.price
