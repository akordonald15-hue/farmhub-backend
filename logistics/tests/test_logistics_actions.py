import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from logistics.models import LogisticsAgent, Vehicle, Dispatch

User = get_user_model()


@pytest.mark.django_db
def test_dispatch_assign_and_set_cost_admin_only(client):
    admin = User.objects.create_superuser(username="admin_log1", password="p", email="admin_log1@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    client.force_login(admin)

    agent_user = User.objects.create_user(email="agent1@example.com", password="StrongPass123", full_name="Agent One")
    agent_user.is_verified = True
    agent_user.save(update_fields=["is_verified"])
    agent = LogisticsAgent.objects.create(full_name="Agent One", user=agent_user)

    vehicle = Vehicle.objects.create(vehicle_type="VAN", registration_number="REG-123")
    dispatch = Dispatch.objects.create(created_by=admin, pickup_address="A", dropoff_address="B")

    r_assign = client.post(
        f"/api/logistics/dispatches/{dispatch.id}/assign/",
        data={"assigned_agent_id": str(agent.id), "assigned_vehicle_id": str(vehicle.id)},
    )
    assert r_assign.status_code == status.HTTP_200_OK

    r_cost = client.post(f"/api/logistics/dispatches/{dispatch.id}/set-cost/", data={"cost": "bad"})
    assert r_cost.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_dispatch_update_status_invalid_and_not_permitted(client):
    admin = User.objects.create_superuser(username="admin_log2", password="p", email="admin_log2@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    dispatch = Dispatch.objects.create(created_by=admin, pickup_address="A", dropoff_address="B")

    client.force_login(admin)
    r_invalid = client.post(f"/api/logistics/dispatches/{dispatch.id}/update-status/", data={"status": "BAD"})
    assert r_invalid.status_code == status.HTTP_400_BAD_REQUEST

    user = User.objects.create_user(email="user_log@example.com", password="StrongPass123", full_name="User Log")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)
    r_forbidden = client.post(f"/api/logistics/dispatches/{dispatch.id}/update-status/", data={"status": "PICKED_UP"})
    assert r_forbidden.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_dispatch_update_status_by_assigned_agent(client):
    admin = User.objects.create_superuser(username="admin_log3", password="p", email="admin_log3@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    agent_user = User.objects.create_user(email="agent2@example.com", password="StrongPass123", full_name="Agent Two")
    agent_user.is_verified = True
    agent_user.save(update_fields=["is_verified"])
    agent = LogisticsAgent.objects.create(full_name="Agent Two", user=agent_user)
    dispatch = Dispatch.objects.create(created_by=admin, assigned_agent=agent, pickup_address="A", dropoff_address="B")

    client.force_login(agent_user)
    r = client.post(
        f"/api/logistics/dispatches/{dispatch.id}/update-status/",
        data={"status": "PICKED_UP", "note": "picked", "location": "lagos"},
    )
    assert r.status_code == status.HTTP_201_CREATED
