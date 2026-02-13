import pytest
from django.utils import timezone
from datetime import timedelta

from reports import services
from accounts.models import User
from orders.models import Order
from reviews.models import Review
from products.models import Category, MenuItem


@pytest.mark.django_db
def test_report_services_basic():
    now = timezone.now()
    start = now - timedelta(days=1)
    end = now + timedelta(days=1)

    user = User.objects.create_user(email="report@example.com", password="p", full_name="Report User")
    order = Order.objects.create(user=user, total_price=100)
    category = Category.objects.create(name="Rice", slug="rice")
    item = MenuItem.objects.create(category=category, name="Jollof", slug="jollof", price=10)
    Review.objects.create(user=user, menu_item=item, rating=4, text="Good")

    users = services.get_user_report(start, end)
    orders = services.get_order_report(start, end)
    reviews = services.get_review_report(start, end)
    payments = services.get_payment_report(start, end)

    assert "total_users" in users
    assert "total_orders" in orders
    assert "total_reviews" in reviews
    assert "total_amount" in payments
