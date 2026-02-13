import logging
from django.template import Template, Context
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

def send_email_notification(user, subject, body_text, body_html=None):
    email = getattr(user, 'email', None)
    if not email:
        logger.warning(f"User {user} has no email address.")
        return False
    try:
        if body_html:
            msg = EmailMultiAlternatives(subject, body_text, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(body_html, "text/html")
            msg.send()
        else:
            send_mail(subject, body_text, settings.DEFAULT_FROM_EMAIL, [email])
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False

def send_push_notification(user, body_text):
    # Firebase-ready stub
    logger.info(f"Push notification to {user}: {body_text}")
    return True

def resend_user_notifications(user_notifications):
    count = 0
    for un in user_notifications:
        user = un.user
        notification = un.notification
        context = notification.payload.copy()
        context['user'] = user
        results = dispatch_notification(user, notification, [un.channel], context)
        if results.get(un.channel) == NotificationStatus.SENT:
            un.status = NotificationStatus.SENT
            un.sent_at = timezone.now()
            un.error_message = ''
            un.save(update_fields=['status', 'sent_at', 'error_message'])
            count += 1
    return count


from .models import (
    Notification,
    UserNotification,
    NotificationTemplate,
    NotificationChannel,
    NotificationStatus,
)

logger = logging.getLogger("notifications")
class NotificationDispatchError(Exception):
    """Custom exception for notification dispatch failures"""
    pass

def render_notification_template(event, channel, context):
    try:
        template = NotificationTemplate.objects.get(
            event=event,
            channel=channel,
            is_active=True
        )
    except NotificationTemplate.DoesNotExist:
        raise NotificationDispatchError(
            f"No active template for event={event}, channel={channel}"
        )

    subject = Template(template.subject).render(Context(context)) if template.subject else ""
    body_text = Template(template.body_text).render(Context(context))
    body_html = Template(template.body_html).render(Context(context)) if template.body_html else None

    return subject, body_text, body_html
def _get_user_phone(user):
    for attr in ['customerprofile', 'farmerprofile', 'vendorprofile', 'logisticsagentprofile']:
        profile = getattr(user, attr, None)
        if profile and profile.phone:
            return profile.phone
    return None
def send_sms_notification(user, body_text):
    phone = _get_user_phone(user)
    if not phone:
        logger.warning(f"User {user.id} has no phone number.")
        return False

    # Termii / Twilio integration goes here
    logger.info(f"SMS to {phone}: {body_text}")
    return True
def dispatch_notification(user, notification, channels, context):
    results = {}

    for channel in channels:
        if channel not in NotificationChannel.values:
            raise ValidationError(f"Invalid notification channel: {channel}")

        # Prevent duplicates
        if UserNotification.objects.filter(
            user=user,
            notification=notification,
            channel=channel
        ).exists():
            logger.info(
                f"Notification already sent: user={user.id}, event={notification.event}, channel={channel}"
            )
            results[channel] = NotificationStatus.SENT
            continue

        try:
            subject, body_text, body_html = render_notification_template(
                notification.event,
                channel,
                context
            )

            if channel == NotificationChannel.EMAIL:
                success = send_email_notification(user, subject, body_text, body_html)

            elif channel == NotificationChannel.SMS:
                success = send_sms_notification(user, body_text)

            elif channel == NotificationChannel.PUSH:
                success = send_push_notification(user, body_text)

            elif channel == NotificationChannel.IN_APP:
                success = True

            status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            sent_at = timezone.now() if success else None
            error_message = "" if success else "Dispatch failed"

        except Exception as e:
            logger.exception("Notification dispatch failed")
            status = NotificationStatus.FAILED
            sent_at = None
            error_message = str(e)

        UserNotification.objects.create(
            user=user,
            notification=notification,
            channel=channel,
            status=status,
            sent_at=sent_at,
            error_message=error_message
        )

        results[channel] = status

    return results
def build_and_send_notification(event, users, payload, channels, context=None):
    context = context or {}

    with transaction.atomic():
        notification = Notification.objects.create(
            event=event,
            payload=payload
        )

        for user in users:
            dispatch_notification(
                user=user,
                notification=notification,
                channels=channels,
                context={**payload, **context, "user": user}
            )

    return notification
