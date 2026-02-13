import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from logistics.models import Dispatch, LogisticsAgent

User = get_user_model()


@pytest.mark.django_db
def test_dispatch_update_status_not_permitted(client):
    user = User.objects.create_user(email="agent@example.com", password="p", full_name="Agent")
    other = User.objects.create_user(email="other@example.com", password="p", full_name="Other")
    agent = LogisticsAgent.objects.create(full_name="Agent L", user=user)
    dispatch = Dispatch.objects.create(reference_code="refx", assigned_agent=agent)

    client.force_login(other)
    r = client.post(f"/api/logistics/dispatches/{dispatch.id}/update-status/", data={"status": "PICKED_UP"})
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_delivery_not_permitted(client):
    user = User.objects.create_user(email="agent2@example.com", password="p", full_name="Agent2")
    other = User.objects.create_user(email="other2@example.com", password="p", full_name="Other2")
    agent = LogisticsAgent.objects.create(full_name="Agent L2", user=user)
    dispatch = Dispatch.objects.create(reference_code="refy", assigned_agent=agent)

    client.force_login(other)
    r = client.post(f"/api/logistics/dispatches/{dispatch.id}/confirm-delivery/", data={"receiver_name": "Bob"})
    assert r.status_code == status.HTTP_403_FORBIDDEN
