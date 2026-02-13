from django.db import models
from django.conf import settings
from django.utils import timezone

class NotificationChannel(models.TextChoices):
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    PUSH = 'push', 'Push'
    IN_APP = 'in_app', 'In App'

class NotificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    READ = 'read', 'Read'

class NotificationTemplate(models.Model):
    event = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, choices=NotificationChannel.choices)
    subject = models.CharField(max_length=255, blank=True)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'channel')
        indexes = [models.Index(fields=['event', 'channel'])]

    def __str__(self):
        return f"{self.event} [{self.channel}]"

class Notification(models.Model):
    event = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='user_notifications')
    channel = models.CharField(max_length=16, choices=NotificationChannel.choices)
    status = models.CharField(
        max_length=16,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status', 'channel']),
            models.Index(fields=['status'])
        ]
        ordering = ['-created_at']

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = NotificationStatus.READ
            self.save(update_fields=['read_at', 'status'])
