import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from accounts.models import User
from orders.models import Order
from payments.models import Payment
from reviews.models import Review

from .models import NotificationChannel
from .services import build_and_send_notification

logger = logging.getLogger("notifications")
@receiver(post_save, sender=User, dispatch_uid="notify_user_registered")
def notify_user_registered(sender, instance, created, **kwargs):
    if not created:
        return

    build_and_send_notification(
        event="user_registered",
        users=[instance],
        payload={
            "user_id": instance.id,
            "email": instance.email,
        },
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
        ],
    )
@receiver(post_save, sender=User, dispatch_uid="notify_email_verified")
def notify_email_verified(sender, instance, **kwargs):
    if not instance.is_verified:
        return

    # Prevent duplicate notifications by checking for existing UserNotification
    from .models import Notification, UserNotification
    existing = UserNotification.objects.filter(
        user=instance,
        notification__event="email_verified",
        channel=NotificationChannel.IN_APP
    ).exists()
    if existing:
        return

    build_and_send_notification(
        event="email_verified",
        users=[instance],
        payload={
            "user_id": instance.id,
        },
        channels=[NotificationChannel.IN_APP],
    )
@receiver(post_save, sender=Order, dispatch_uid="notify_order_created")
def notify_order_created(sender, instance, created, **kwargs):
    if not created:
        return

    build_and_send_notification(
        event="order_created",
        users=[instance.user],
        payload={
            "order_id": instance.id,
            "status": instance.status,
        },
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
        ],
    )
@receiver(post_save, sender=Payment, dispatch_uid="notify_payment_status")
def notify_payment_status(sender, instance, created, **kwargs):
    if created:
        return  # created == pending

    if instance.status == "failed":
        event = "payment_failed"
    elif instance.status == "paid":
        event = "order_paid"
    else:
        return

    build_and_send_notification(
        event=event,
        users=[instance.user],
        payload={
            "payment_id": instance.id,
            "amount": instance.amount,
        },
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
        ],
    )
@receiver(post_save, sender=Review, dispatch_uid="notify_review_submitted")
def notify_review_submitted(sender, instance, created, **kwargs):
    if not created:
        return

    build_and_send_notification(
        event="review_submitted",
        users=[instance.user],
        payload={
            "review_id": instance.id,
            "rating": instance.rating,
        },
        channels=[NotificationChannel.IN_APP],
    )
