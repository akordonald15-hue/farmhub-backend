import pytest
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem

User = get_user_model()


@pytest.mark.django_db
def test_order_and_orderitem_str_and_line_total():
    user = User.objects.create_user(username="order_model_user", password="p")
    order = Order.objects.create(user=user, total_price=10)
    assert f"Order #{order.id}" in str(order)

    item = OrderItem.objects.create(order=order, menu_item=None, quantity=2, price=10)
    assert item.line_total() == 20
    assert "Deleted Item" in str(item)
