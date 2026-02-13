import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_paystack_webhook_invalid_reference():
    client = APIClient()
    r = client.post("/api/orders/paystack_webhook/", data={"reference": "missing"}, format="json")
    assert r.status_code == status.HTTP_404_NOT_FOUND
    assert r.json().get("error") == "Order not found."
