from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from accounts.permissions import IsEmailVerified
from rest_framework.pagination import PageNumberPagination

from .models import UserNotification, NotificationStatus, NotificationChannel
from .serializers import UserNotificationSerializer
from .tasks import send_notification_task
from .services import resend_user_notifications

User = get_user_model()


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationViewSet(viewsets.GenericViewSet):
    """
    ViewSet for UserNotifications and admin broadcast/resend actions.
    """
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]
    pagination_class = NotificationPagination
    queryset = UserNotification.objects.all()

    def get_queryset(self):
        # Users only see their notifications
        return (
            UserNotification.objects
            .filter(user=self.request.user)
            .select_related("notification")
            .order_by("-created_at")
        )

    @action(detail=False, methods=["get"], url_path="my")
    def list_user_notifications(self, request):
        """List notifications for logged-in user"""
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = get_object_or_404(
            UserNotification,
            pk=pk,
            user=request.user,
            status=NotificationStatus.PENDING
        )
        notification.status = NotificationStatus.READ
        notification.read_at = timezone.now()
        notification.save(update_fields=["status", "read_at"])
        return Response({"status": "read"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read(self, request):
        """Mark all pending notifications as read"""
        updated = (
            UserNotification.objects
            .filter(user=request.user, status=NotificationStatus.PENDING)
            .update(status=NotificationStatus.READ, read_at=timezone.now())
        )
        return Response({"status": "all_read", "count": updated}, status=status.HTTP_200_OK)

    # --- Admin-only actions ---
    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser, IsEmailVerified], url_path="broadcast")
    def broadcast(self, request):
        """Admin broadcast to users"""
        event = request.data.get("event")
        message = request.data.get("message")
        channels = request.data.get("channels", [])
        role = request.data.get("role")

        if not event or not message:
            return Response({"error": "event and message are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate channels
        valid_channels = {c[0] for c in NotificationChannel.choices}
        invalid = set(channels) - valid_channels
        if invalid:
            return Response({"error": f"Invalid channels: {list(invalid)}"}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(is_active=True)
        if role:
            if not hasattr(User, "ROLE_CHOICES"):
                return Response({"error": "User role system not configured"}, status=status.HTTP_400_BAD_REQUEST)
            users = users.filter(role=role)

        user_ids = list(users.values_list("id", flat=True))
        if not user_ids:
            return Response({"error": "No users found for broadcast"}, status=status.HTTP_400_BAD_REQUEST)

        # Queue Celery task
        send_notification_task.delay(event=event, user_ids=user_ids, payload={"message": message}, channels=channels)

        return Response({"status": "broadcast_queued", "users": len(user_ids)}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser, IsEmailVerified], url_path="resend-failed")
    def resend_failed(self, request):
        """Resend all failed notifications"""
        failed = UserNotification.objects.filter(status=NotificationStatus.FAILED)
        count = resend_user_notifications(failed)
        return Response({"status": "resent", "count": count}, status=status.HTTP_200_OK)
