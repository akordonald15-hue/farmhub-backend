from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import Order
from .serializers import OrderSerializer
import logging
from accounts.permissions import IsEmailVerified
from core.logging_utils import log_event

admin_logger = logging.getLogger('admin_actions')


# ----------------------------
# Permissions
# ----------------------------
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow authenticated users to access the view.
    Allow owners to access their orders.
    Allow staff/admins to access all orders.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

# ----------------------------
# Throttle for Admin
# ----------------------------
class AdminThrottle(UserRateThrottle):
    rate = '50/hour'


# ----------------------------
# Order Create API (Dedicated endpoint for clarity)
# ----------------------------
class OrderCreateAPIView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()  # ✅ Just save()

        log_event("order_events", request, "order_create", "success", user=request.user, extra={"order_id": order.id})
        return Response({
            "success": True,
            "message": "Order created successfully",
            "data": OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)

# ----------------------------
# Order ViewSet (List/Retrieve/Update for admin/user)
# ----------------------------
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmailVerified, IsOwnerOrAdmin]
    queryset = Order.objects.all().order_by('-created_at')

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()  # ✅ Just save()

    # ----------------------------
    # Admin manually updates status
    # ----------------------------
    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAdminUser, IsEmailVerified],
        throttle_classes=[AdminThrottle]
    )
    def update_status(self, request, pk=None):
        order = self.get_object()
        old_status = order.status
        new_status = request.data.get('status')

        if not new_status:
            log_event("order_events", request, "order_status_update", "failure", user=request.user, extra={"order_id": order.id})
            return Response(
                {'error': 'Status field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        admin_logger.info(
            f"Admin {request.user.username} updated order {order.id} "
            f"status from '{old_status}' to '{new_status}'"
        )
        log_event(
            "order_events",
            request,
            "order_status_update",
            "success",
            user=request.user,
            extra={"order_id": order.id, "old_status": old_status, "new_status": new_status},
        )

        return Response(
            {'message': f'Order status updated to {new_status}'},
            status=status.HTTP_200_OK
        )

    # ----------------------------
    # Paystack Webhook
    # ----------------------------
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def paystack_webhook(self, request):
        reference = request.data.get('reference')

        if not reference:
            log_event("order_events", request, "paystack_webhook", "failure")
            return Response(
                {'error': 'Reference is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(paystack_reference=reference)
            order.paid = True
            order.status = 'PROCESSING'
            order.save()

            log_event("order_events", request, "paystack_webhook", "success", user=order.user, extra={"order_id": order.id})
            return Response(
                {'message': 'Order payment verified and updated.'},
                status=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            log_event("order_events", request, "paystack_webhook", "failure")
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
