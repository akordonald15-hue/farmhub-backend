import pytest

from marketplace.task import send_low_stock_alerts
from marketplace.models import Product, Category
from farmers.models import Farmer


@pytest.mark.django_db
def test_send_low_stock_alerts(monkeypatch):
    farmer = Farmer.objects.create(contact_name="Farmer Alert", email="farmer@example.com")
    category = Category.objects.create(name="Cat", slug="cat")
    Product.objects.create(
        farmer=farmer,
        title="Beans",
        slug="beans",
        category=category,
        price="10.00",
        quantity="1.000",
        min_order="1.000",
        is_active=True,
    )

    sent = {"count": 0}
    def fake_send_mail(*args, **kwargs):
        sent["count"] += 1

    monkeypatch.setattr("marketplace.task.send_mail", fake_send_mail)
    result = send_low_stock_alerts(threshold=2)
    assert result["alerts_sent"] == 1
