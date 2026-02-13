from django.contrib import admin
from django.utils import timezone
from .models import Notification, UserNotification, NotificationTemplate

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'created_at')
    search_fields = ('event',)
    list_filter = ('event', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'notification', 'channel', 'status', 'sent_at', 'read_at', 'created_at', 'updated_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('user__email', 'notification__event')
    actions = ['mark_as_read', 'retry_failed']
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'read_at', 'error_message')

    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read', read_at=timezone.now())
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"

    def retry_failed(self, request, queryset):
        from .services import resend_user_notifications
        failed = queryset.filter(status='failed')
        count = resend_user_notifications(failed)
        self.message_user(request, f"Retried {count} failed notifications.")
    retry_failed.short_description = "Retry failed notifications"

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'channel', 'is_active', 'created_at', 'updated_at')
    list_filter = ('channel', 'event', 'is_active', 'created_at')
    search_fields = ('event', 'subject')
    readonly_fields = ('created_at', 'updated_at')
