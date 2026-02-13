import pytest
from django.contrib.auth import get_user_model

from logistics import services
from logistics.models import LogisticsAgent, Vehicle, Dispatch
from orders.models import Order
from products.models import Category, MenuItem
from orders.models import OrderItem

User = get_user_model()


@pytest.mark.django_db
def test_logistics_service_flow():
    user = User.objects.create_user(email="svc@example.com", password="p", full_name="Svc")
    agent = LogisticsAgent.objects.create(full_name="Agent Svc")
    vehicle = Vehicle.objects.create(vehicle_type="VAN", registration_number="REG123")

    category = Category.objects.create(name="Wraps", slug="wraps")
    item = MenuItem.objects.create(category=category, name="Wrap", slug="wrap", price=100)
    order = Order.objects.create(user=user, total_price=100)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1, price=item.price)

    dispatch = services.create_dispatch_from_order(order, created_by=user)
    assert dispatch.reference_code.startswith("ORD-")

    dispatch = services.assign_agent(dispatch.id, agent.id, vehicle.id, assigned_by=user)
    assert dispatch.status == "ASSIGNED"

    status_log = services.update_dispatch_status(dispatch.id, "PICKED_UP", updated_by=user)
    assert status_log.status == "PICKED_UP"

    confirmed = services.confirm_delivery(dispatch.id, receiver_name="Bob", updated_by=user)
    assert confirmed.status == "DELIVERED"


def test_calculate_logistics_cost():
    assert services.calculate_logistics_cost(2, "VAN") == 400
