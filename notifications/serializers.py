from rest_framework import serializers
from .models import Notification, UserNotification, NotificationChannel, NotificationStatus

class NotificationSerializer(serializers.ModelSerializer):
    """
    INTERNAL serializer.
    Should rarely be exposed directly to frontend.
    """
    class Meta:
        model = Notification
        fields = ['id', 'event', 'created_at']
        read_only_fields = fields
class UserNotificationSerializer(serializers.ModelSerializer):
    event = serializers.CharField(source='notification.event', read_only=True)
    channel_label = serializers.CharField(source='get_channel_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserNotification
        fields = [
            'id',
            'event',
            'channel',
            'channel_label',
            'status',
            'status_label',
            'sent_at',
            'read_at',
            'error_message',
        ]
        read_only_fields = fields
class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
