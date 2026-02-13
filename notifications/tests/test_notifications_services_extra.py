import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from notifications.models import Notification, NotificationTemplate, NotificationChannel, NotificationStatus
from notifications.services import (
    send_email_notification,
    dispatch_notification,
)

User = get_user_model()


def test_send_email_notification_missing_email():
    class Dummy:
        email = None
        id = "dummy"

    assert send_email_notification(Dummy(), "subject", "body") is False


@pytest.mark.django_db
def test_dispatch_notification_in_app_creates_user_notification():
    user = User.objects.create_user(email="notify2@example.com", password="StrongPass123", full_name="Notify2")
    notification = Notification.objects.create(event="order.created", payload={"id": 1})
    NotificationTemplate.objects.create(
        event="order.created",
        channel=NotificationChannel.IN_APP,
        subject="Order {{ user.id }}",
        body_text="Hello {{ user.id }}",
        body_html="",
        is_active=True,
    )

    results = dispatch_notification(user, notification, [NotificationChannel.IN_APP], {"user": user})
    assert results[NotificationChannel.IN_APP] == NotificationStatus.SENT


@pytest.mark.django_db
def test_dispatch_notification_invalid_channel_raises():
    user = User.objects.create_user(email="notify3@example.com", password="StrongPass123", full_name="Notify3")
    notification = Notification.objects.create(event="order.created", payload={"id": 2})
    with pytest.raises(ValidationError):
        dispatch_notification(user, notification, ["invalid_channel"], {"user": user})
