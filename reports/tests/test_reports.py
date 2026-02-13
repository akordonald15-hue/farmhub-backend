import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from reports.views import parse_date_range
from rest_framework.exceptions import ValidationError

User = get_user_model()


def test_parse_date_range_custom_requires_dates():
    request = type("Req", (), {"query_params": {"period": "custom"}})()
    with pytest.raises(ValidationError):
        parse_date_range(request)


@pytest.mark.django_db
def test_reports_endpoints_daily():
    admin = User.objects.create_superuser(username="admin_r", password="p", email="admin_r@test.com")
    client = APIClient()
    client.force_login(admin)

    r_dashboard = client.get("/api/reports/dashboard/?period=daily")
    assert r_dashboard.status_code == status.HTTP_200_OK

    r_users = client.get("/api/reports/users/?period=daily")
    assert r_users.status_code == status.HTTP_200_OK

    r_orders = client.get("/api/reports/orders/?period=daily")
    assert r_orders.status_code == status.HTTP_200_OK

    r_payments = client.get("/api/reports/payments/?period=daily")
    assert r_payments.status_code == status.HTTP_200_OK

    r_reviews = client.get("/api/reports/reviews/?period=daily")
    assert r_reviews.status_code == status.HTTP_200_OK
