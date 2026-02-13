from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAdminUser
from accounts.permissions import IsEmailVerified
from django.core.cache import cache
import logging

from .models import MenuItem
from .serializers import MenuItemSerializer
from core.logging_utils import log_event

# Logger
admin_logger = logging.getLogger('admin_actions')

# Cache key
CACHE_KEY = "public_menu_list_v1"


class AdminThrottle(UserRateThrottle):
    rate = '50/hour'  # max 50 admin actions per hour


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ADMIN-ONLY MENU ENDPOINTS
    Create, update, delete menu items.
    Auto-clear public cache after any admin change.
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser, IsEmailVerified]  # Only admin can modify menu

    # Clear cache on create
    def perform_create(self, serializer):
        item = serializer.save()
        cache.delete(CACHE_KEY)
        admin_logger.info(f"Admin {self.request.user} created menu item {item.id}")
        log_event("admin_actions", self.request, "menu_create", "success", user=self.request.user, extra={"item_id": item.id})
        return item

    # Clear cache on update
    def perform_update(self, serializer):
        item = serializer.save()
        cache.delete(CACHE_KEY)
        admin_logger.info(f"Admin {self.request.user} updated menu item {item.id}")
        log_event("admin_actions", self.request, "menu_update", "success", user=self.request.user, extra={"item_id": item.id})
        return item

    # Clear cache on delete
    def perform_destroy(self, instance):
        admin_logger.info(f"Admin {self.request.user} deleted menu item {instance.id}")
        log_event("admin_actions", self.request, "menu_delete", "success", user=self.request.user, extra={"item_id": instance.id})
        cache.delete(CACHE_KEY)
        instance.delete()

    # Custom PATCH action: update availability
    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAdminUser, IsEmailVerified],
        throttle_classes=[AdminThrottle]
    )
    def update_status(self, request, pk=None):
        item = self.get_object()
        old_status = item.is_available

        new_status = request.data.get('is_available')
        item.is_available = new_status
        item.save()

        # Clear public cache
        cache.delete(CACHE_KEY)

        admin_logger.info(
            f"Admin {request.user.username} updated availability of item {item.id} "
            f"from {old_status} to {new_status}"
        )
        log_event(
            "admin_actions",
            request,
            "menu_status_update",
            "success",
            user=request.user,
            extra={"item_id": item.id, "old_status": old_status, "new_status": new_status},
        )

        return Response({
            "message": "Status updated",
            "old_status": old_status,
            "new_status": new_status
        })


class MenuViewSet(viewsets.ModelViewSet):
    """
    Public list/retrieve for available items.
    Admin-only create/update/delete and status updates.
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        if self.action in ["list", "retrieve"]:
            return MenuItem.objects.filter(is_available=True).select_related("category")
        return MenuItem.objects.all()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser(), IsEmailVerified()]

    def perform_create(self, serializer):
        item = serializer.save()
        cache.delete(CACHE_KEY)
        admin_logger.info(f"Admin {self.request.user} created menu item {item.id}")
        log_event("admin_actions", self.request, "menu_create", "success", user=self.request.user, extra={"item_id": item.id})
        return item

    def perform_update(self, serializer):
        item = serializer.save()
        cache.delete(CACHE_KEY)
        admin_logger.info(f"Admin {self.request.user} updated menu item {item.id}")
        log_event("admin_actions", self.request, "menu_update", "success", user=self.request.user, extra={"item_id": item.id})
        return item

    def perform_destroy(self, instance):
        admin_logger.info(f"Admin {self.request.user} deleted menu item {instance.id}")
        log_event("admin_actions", self.request, "menu_delete", "success", user=self.request.user, extra={"item_id": instance.id})
        cache.delete(CACHE_KEY)
        instance.delete()

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[permissions.IsAdminUser, IsEmailVerified],
        throttle_classes=[AdminThrottle],
    )
    def update_status(self, request, pk=None):
        item = self.get_object()
        old_status = item.is_available
        new_status = request.data.get("is_available")
        item.is_available = new_status
        item.save()

        cache.delete(CACHE_KEY)
        admin_logger.info(
            f"Admin {request.user.username} updated availability of item {item.id} "
            f"from {old_status} to {new_status}"
        )
        log_event(
            "admin_actions",
            request,
            "menu_status_update",
            "success",
            user=request.user,
            extra={"item_id": item.id, "old_status": old_status, "new_status": new_status},
        )
        log_event(
            "admin_actions",
            request,
            "menu_status_update",
            "success",
            user=request.user,
            extra={"item_id": item.id, "old_status": old_status, "new_status": new_status},
        )

        return Response(
            {
                "message": "Status updated",
                "old_status": old_status,
                "new_status": new_status,
            }
        )
