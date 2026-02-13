import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from menu.models import Category, MenuItem
from orders.models import Order
from orders.serializers import OrderSerializer

User = get_user_model()


@pytest.mark.django_db
def test_order_serializer_create_with_menu_id():
    user = User.objects.create_user(username="order_ser_user", password="p")
    category = Category.objects.create(name="Wraps4", slug="wraps4")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 4",
        slug="chicken-wrap-4",
        description="Tasty",
        price=1200,
        is_available=True,
    )

    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    data = {
        "items": [{"menu_id": menu_item.id, "quantity": 1}],
        "address": "12345 Street",
        "phone": "12345678",
    }
    serializer = OrderSerializer(context={"request": request})
    order = serializer.create(validated_data=data)
    assert order.total_price == menu_item.price


@pytest.mark.django_db
def test_order_serializer_rejects_unavailable_item():
    user = User.objects.create_user(username="order_ser_user2", password="p")
    category = Category.objects.create(name="Wraps5", slug="wraps5")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 5",
        slug="chicken-wrap-5",
        description="Tasty",
        price=1200,
        is_available=False,
    )

    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    data = {"items": [{"menu_item": menu_item.id, "quantity": 1}]}
    serializer = OrderSerializer(data=data, context={"request": request})
    assert serializer.is_valid(raise_exception=True)
    with pytest.raises(serializers.ValidationError):
        serializer.save()


@pytest.mark.django_db
def test_order_serializer_rejects_invalid_quantity_and_short_address():
    user = User.objects.create_user(username="order_ser_user3", password="p")
    category = Category.objects.create(name="Wraps6", slug="wraps6")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 6",
        slug="chicken-wrap-6",
        description="Tasty",
        price=1200,
        is_available=True,
    )

    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    data = {"items": [{"menu_item": menu_item.id, "quantity": 0}], "address": "12345 Street", "phone": "12345678"}
    serializer = OrderSerializer(data=data, context={"request": request})
    assert serializer.is_valid(raise_exception=True)
    with pytest.raises(serializers.ValidationError):
        serializer.save()


@pytest.mark.django_db
def test_order_serializer_requires_items():
    user = User.objects.create_user(username="order_ser_user4", password="p")
    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    serializer = OrderSerializer(data={"items": []}, context={"request": request})
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_order_serializer_rejects_short_address():
    user = User.objects.create_user(username="order_ser_user5", password="p")
    category = Category.objects.create(name="Wraps7", slug="wraps7")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 7",
        slug="chicken-wrap-7",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    data = {"items": [{"menu_item": menu_item.id, "quantity": 1}], "address": "123", "phone": "12345678"}
    serializer = OrderSerializer(data=data, context={"request": request})
    with pytest.raises(serializers.ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_order_serializer_create_with_menu_item_instance():
    user = User.objects.create_user(username="order_ser_user6", password="p")
    category = Category.objects.create(name="Wraps8", slug="wraps8")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 8",
        slug="chicken-wrap-8",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    serializer = OrderSerializer(context={"request": request})
    order = serializer.create(
        validated_data={"items": [{"menu_item": menu_item, "quantity": 1}], "address": "12345 Street", "phone": "12345678"}
    )
    assert order.total_price == menu_item.price


@pytest.mark.django_db
def test_order_serializer_update_ignores_items():
    user = User.objects.create_user(username="order_ser_user7", password="p")
    order = Order.objects.create(user=user, total_price=0, address="Old", phone="12345678")
    serializer = OrderSerializer()
    updated = serializer.update(order, {"address": "New", "items": [{"menu_item": 1, "quantity": 1}]})
    assert updated.address == "New"


def test_order_serializer_validate_allows_none_values():
    serializer = OrderSerializer()
    assert serializer.validate_address(None) is None
    assert serializer.validate_phone(None) is None


@pytest.mark.django_db
def test_order_serializer_create_with_menu_item_id_int():
    user = User.objects.create_user(username="order_ser_user8", password="p")
    category = Category.objects.create(name="Wraps9", slug="wraps9")
    menu_item = MenuItem.objects.create(
        category=category,
        name="Chicken Wrap 9",
        slug="chicken-wrap-9",
        description="Tasty",
        price=1200,
        is_available=True,
    )
    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    serializer = OrderSerializer(context={"request": request})
    order = serializer.create(
        validated_data={"items": [{"menu_item": menu_item.id, "quantity": 1}], "address": "12345 Street", "phone": "12345678"}
    )
    assert order.total_price == menu_item.price


@pytest.mark.django_db
def test_order_serializer_rejects_invalid_menu_item_entry():
    user = User.objects.create_user(username="order_ser_user9", password="p")
    factory = APIRequestFactory()
    request = factory.post("/api/orders/create/")
    request.user = user
    serializer = OrderSerializer(context={"request": request})
    with pytest.raises(serializers.ValidationError):
        serializer.create(validated_data={"items": [{"quantity": 1}], "address": "12345 Street", "phone": "12345678"})
