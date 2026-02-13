import pytest
from django.contrib.auth import get_user_model

from notifications.models import NotificationTemplate, NotificationChannel
from notifications import signals

User = get_user_model()


@pytest.mark.django_db
def test_notify_user_registered_signal():
    user = User.objects.create_user(email="sig@example.com", password="p", full_name="Sig User")
    NotificationTemplate.objects.create(
        event="user_registered",
        channel=NotificationChannel.EMAIL,
        subject="Welcome",
        body_text="Hello {{ user.email }}",
        body_html="",
        is_active=True,
    )
    NotificationTemplate.objects.create(
        event="user_registered",
        channel=NotificationChannel.IN_APP,
        subject="Welcome",
        body_text="Hello {{ user.email }}",
        body_html="",
        is_active=True,
    )

    signals.notify_user_registered(sender=User, instance=user, created=True)
