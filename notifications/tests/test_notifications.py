import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from notifications.models import Notification, UserNotification, NotificationStatus

User = get_user_model()


@pytest.mark.django_db
def test_user_can_list_and_mark_notifications(client):
    user = User.objects.create_user(email="notify@example.com", password="StrongPass123", full_name="Notify User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    n = Notification.objects.create(event="order.created", payload={"id": 1})
    un = UserNotification.objects.create(user=user, notification=n, channel="in_app", status=NotificationStatus.PENDING)

    r_list = client.get("/api/notifications/notifications/my/")
    assert r_list.status_code == status.HTTP_200_OK

    r_read = client.post(f"/api/notifications/notifications/{un.id}/read/")
    assert r_read.status_code == status.HTTP_200_OK

    r_all = client.post("/api/notifications/notifications/read-all/")
    assert r_all.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_broadcast_invalid_channel(client):
    admin = User.objects.create_superuser(username="admin_notify", password="p", email="admin_notify@test.com")
    client.force_login(admin)
    payload = {"event": "test", "message": "hello", "channels": ["invalid"]}
    r = client.post("/api/notifications/notifications/broadcast/", data=payload, format="json")
    assert r.status_code == status.HTTP_400_BAD_REQUEST
