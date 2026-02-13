import json

import pytest
from rest_framework import status


@pytest.mark.django_db
def test_paystack_webhook_missing_signature(client):
    payload = {"event": "charge.success", "data": {"reference": "ref", "metadata": {"order_id": "1"}}}
    r = client.post("/api/payments/webhook/", data=payload, content_type="application/json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_paystack_webhook_invalid_signature(client, settings):
    settings.PAYSTACK_SECRET_KEY = "secret"
    payload = {"event": "charge.success", "data": {"reference": "ref", "metadata": {"order_id": "1"}}}
    body = json.dumps(payload).encode("utf-8")
    headers = {"HTTP_X_PAYSTACK_SIGNATURE": "bad-signature"}
    r = client.post("/api/payments/webhook/", data=body, content_type="application/json", **headers)
    assert r.status_code == status.HTTP_403_FORBIDDEN
