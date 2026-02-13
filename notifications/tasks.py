import logging
try:
    from celery import shared_task
except ImportError:  # pragma: no cover - optional dependency for tests
    def shared_task(*dargs, **dkwargs):
        def decorator(func):
            def delay(*args, **kwargs):
                return func(*args, **kwargs)
            func.delay = delay
            return func
        return decorator
from django.contrib.auth import get_user_model

from .models import NotificationChannel
from .services import build_and_send_notification

logger = logging.getLogger("notifications.tasks")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    retry_backoff=True,
)
def send_notification_task(self, event, user_ids, payload, channels):
    """
    Celery task to asynchronously dispatch notifications.

    Args:
        event (str): Notification event key
        user_ids (list[int]): Target user IDs
        payload (dict): Event payload
        channels (list[str]): Notification channels
    """
    User = get_user_model()

    # Validate channels
    valid_channels = {choice[0] for choice in NotificationChannel.choices}
    invalid = set(channels) - valid_channels
    if invalid:
        logger.error(f"Invalid notification channels: {invalid}")
        return

    users = User.objects.filter(id__in=user_ids, is_active=True)

    if not users.exists():
        logger.warning(f"No valid users found for notification event={event}")
        return

    logger.info(
        f"Dispatching notification event='{event}' "
        f"to users={list(users.values_list('id', flat=True))} "
        f"via channels={channels}"
    )

    build_and_send_notification(
        event=event,
        users=users,
        payload=payload,
        channels=channels,
    )

    logger.info(f"Notification event='{event}' dispatched successfully")
