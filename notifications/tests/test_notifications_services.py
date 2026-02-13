import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from notifications.models import NotificationTemplate, NotificationChannel
from notifications import services

User = get_user_model()


@pytest.mark.django_db
def test_render_notification_template_and_dispatch():
    user = User.objects.create_user(email="notify_svc@example.com", password="p", full_name="Notify Svc")
    NotificationTemplate.objects.create(
        event="test.event",
        channel=NotificationChannel.IN_APP,
        subject="Hi",
        body_text="Hello {{ user.email }}",
        body_html="",
        is_active=True,
    )
    subject, body_text, body_html = services.render_notification_template(
        "test.event", NotificationChannel.IN_APP, {"user": user}
    )
    assert "notify_svc@example.com" in body_text

    notification = services.build_and_send_notification(
        event="test.event",
        users=[user],
        payload={"message": "hi"},
        channels=[NotificationChannel.IN_APP],
    )
    assert notification.event == "test.event"


@pytest.mark.django_db
def test_dispatch_notification_invalid_channel():
    user = User.objects.create_user(email="notify_bad@example.com", password="p", full_name="Notify Bad")
    notification = services.Notification.objects.create(event="bad.event", payload={})
    with pytest.raises(ValidationError):
        services.dispatch_notification(user, notification, ["bad"], {})


@pytest.mark.django_db
def test_send_sms_notification_requires_phone():
    user = User.objects.create_user(email="sms@example.com", password="p", full_name="Sms User")
    assert services.send_sms_notification(user, "hi") is False


@pytest.mark.django_db
def test_resend_user_notifications_updates_status():
    user = User.objects.create_user(email="resend_notify@example.com", password="p", full_name="Resend")
    NotificationTemplate.objects.create(
        event="resend_event",
        channel=NotificationChannel.IN_APP,
        subject="",
        body_text="Hello",
        body_html="",
        is_active=True,
    )
    notification = services.Notification.objects.create(event="resend_event", payload={})
    un = services.UserNotification.objects.create(
        user=user,
        notification=notification,
        channel=NotificationChannel.IN_APP,
        status=services.NotificationStatus.FAILED,
    )
    count = services.resend_user_notifications([un])
    assert count == 1
