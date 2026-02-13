import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from logistics.models import LogisticsAgent, Vehicle, Dispatch

User = get_user_model()


@pytest.mark.django_db
def test_dispatch_assign_and_set_cost(client):
    admin = User.objects.create_superuser(username="admin_l", password="p", email="admin_l@test.com")
    client.force_login(admin)

    agent = LogisticsAgent.objects.create(full_name="Agent A")
    vehicle = Vehicle.objects.create(vehicle_type="VAN", registration_number="ABC123")
    dispatch = Dispatch.objects.create(reference_code="ref1")

    r_assign = client.post(
        f"/api/logistics/dispatches/{dispatch.id}/assign/",
        data={"assigned_agent_id": str(agent.id), "assigned_vehicle_id": str(vehicle.id)},
    )
    assert r_assign.status_code == status.HTTP_200_OK

    r_cost = client.post(f"/api/logistics/dispatches/{dispatch.id}/set-cost/", data={"cost": "12.5"})
    assert r_cost.status_code == status.HTTP_200_OK

    r_cost_bad = client.post(f"/api/logistics/dispatches/{dispatch.id}/set-cost/", data={"cost": "bad"})
    assert r_cost_bad.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_dispatch_update_status_invalid(client):
    admin = User.objects.create_superuser(username="admin_l2", password="p", email="admin_l2@test.com")
    client.force_login(admin)

    dispatch = Dispatch.objects.create(reference_code="ref2")
    r = client.post(f"/api/logistics/dispatches/{dispatch.id}/update-status/", data={"status": "BAD"})
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_dispatch_update_status_and_confirm_delivery(client):
    user = User.objects.create_user(email="agent_ok@example.com", password="p", full_name="Agent OK")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    agent = LogisticsAgent.objects.create(full_name="Agent OK", user=user)
    dispatch = Dispatch.objects.create(reference_code="refok", assigned_agent=agent)

    client.force_login(user)
    r = client.post(f"/api/logistics/dispatches/{dispatch.id}/update-status/", data={"status": "PICKED_UP"})
    assert r.status_code == status.HTTP_201_CREATED

    r2 = client.post(f"/api/logistics/dispatches/{dispatch.id}/confirm-delivery/", data={"receiver_name": "Bob"})
    assert r2.status_code == status.HTTP_200_OK
