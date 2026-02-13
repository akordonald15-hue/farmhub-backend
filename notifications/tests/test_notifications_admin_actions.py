import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from notifications.models import Notification, UserNotification, NotificationStatus

User = get_user_model()


@pytest.mark.django_db
def test_admin_broadcast_missing_event_or_message(client):
    admin = User.objects.create_superuser(username="admin_notify2", password="p", email="admin_notify2@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    client.force_login(admin)

    r_missing_message = client.post(
        "/api/notifications/notifications/broadcast/",
        data={"event": "test", "channels": ["in_app"]},
        format="json",
    )
    assert r_missing_message.status_code == status.HTTP_400_BAD_REQUEST

    r_missing_event = client.post(
        "/api/notifications/notifications/broadcast/",
        data={"message": "hello", "channels": ["in_app"]},
        format="json",
    )
    assert r_missing_event.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_admin_broadcast_no_users_for_role(client):
    admin = User.objects.create_superuser(username="admin_notify3", password="p", email="admin_notify3@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    client.force_login(admin)

    payload = {"event": "test", "message": "hello", "channels": ["in_app"], "role": "customer"}
    r = client.post("/api/notifications/notifications/broadcast/", data=payload, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_admin_resend_failed_uses_service(client, monkeypatch):
    admin = User.objects.create_superuser(username="admin_notify4", password="p", email="admin_notify4@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    client.force_login(admin)

    notification = Notification.objects.create(event="test.event", payload={"id": 1})
    UserNotification.objects.create(
        user=admin,
        notification=notification,
        channel="in_app",
        status=NotificationStatus.FAILED,
    )

    def fake_resend(qs):
        return 2

    monkeypatch.setattr("notifications.views.resend_user_notifications", fake_resend)
    r = client.post("/api/notifications/notifications/resend-failed/")
    assert r.status_code == status.HTTP_200_OK
    assert r.json()["count"] == 2
