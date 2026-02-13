import pytest
from django.contrib.auth import get_user_model

from notifications.models import NotificationTemplate, NotificationChannel
from notifications.tasks import send_notification_task

User = get_user_model()


@pytest.mark.django_db
def test_send_notification_task_runs():
    user = User.objects.create_user(email="task@example.com", password="p", full_name="Task User")
    NotificationTemplate.objects.create(
        event="task_event",
        channel=NotificationChannel.IN_APP,
        subject="",
        body_text="Hello",
        body_html="",
        is_active=True,
    )
    send_notification_task(None, event="task_event", user_ids=[user.id], payload={"message": "hi"}, channels=[NotificationChannel.IN_APP])


@pytest.mark.django_db
def test_send_notification_task_invalid_channel():
    user = User.objects.create_user(email="task2@example.com", password="p", full_name="Task User")
    send_notification_task(None, event="task_event", user_ids=[user.id], payload={"message": "hi"}, channels=["bad"])


@pytest.mark.django_db
def test_send_notification_task_no_users():
    send_notification_task(None, event="task_event", user_ids=[999], payload={"message": "hi"}, channels=[NotificationChannel.IN_APP])
