# logistics/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.permissions import IsEmailVerified

from .models import LogisticsAgent, Vehicle, Dispatch, DispatchStatusUpdate
from .serializers import (
    LogisticsAgentSerializer,
    VehicleSerializer,
    DispatchSerializer,
    DispatchStatusUpdateSerializer,
)


class IsStaffOrAgent(permissions.BasePermission):
    """
    Allow safe methods to anyone, but write methods to staff or logistics agents (linked users).
    """
    def has_permission(self, request, view):
        # Allow safe methods
        if request.method in permissions.SAFE_METHODS:
            return True
        # Must be authenticated for unsafe methods
        return request.user and request.user.is_authenticated

    def is_agent_user(self, user):
        return hasattr(user, "logistics_agent_profile") and user.logistics_agent_profile is not None

    def has_object_permission(self, request, view, obj):
        # Staff (admins) can do anything
        if request.user.is_staff:
            return True
        # Agents can modify their own objects
        if isinstance(obj, LogisticsAgent) and obj.user and obj.user == request.user:
            return True
        if isinstance(obj, Dispatch) and obj.assigned_agent and obj.assigned_agent.user == request.user:
            return True
        if isinstance(obj, DispatchStatusUpdate) and obj.created_by == request.user:
            return True
        return False


class LogisticsAgentViewSet(viewsets.ModelViewSet):
    queryset = LogisticsAgent.objects.all()
    serializer_class = LogisticsAgentSerializer
    permission_classes = [IsStaffOrAgent, IsEmailVerified]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save()


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("driver").all()
    serializer_class = VehicleSerializer
    permission_classes = [IsStaffOrAgent, IsEmailVerified]


class DispatchViewSet(viewsets.ModelViewSet):
    queryset = Dispatch.objects.select_related("assigned_agent", "assigned_vehicle").all()
    serializer_class = DispatchSerializer
    permission_classes = [IsStaffOrAgent, IsEmailVerified]

    def perform_create(self, serializer):
        # set created_by automatically
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    @action(detail=True, methods=["post"], url_path="assign", permission_classes=[permissions.IsAdminUser, IsEmailVerified])
    def assign(self, request, pk=None):
        """
        Admin-only: assign an agent and optionally a vehicle to a dispatch.
        Payload: {"assigned_agent_id": "<uuid>", "assigned_vehicle_id": "<uuid>"}
        """
        dispatch = self.get_object()
        agent_id = request.data.get("assigned_agent_id")
        vehicle_id = request.data.get("assigned_vehicle_id")
        if agent_id:
            agent = get_object_or_404(LogisticsAgent, pk=agent_id)
            dispatch.assigned_agent = agent
        if vehicle_id:
            vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
            dispatch.assigned_vehicle = vehicle
        dispatch.status = "ASSIGNED"
        dispatch.save(update_fields=["assigned_agent", "assigned_vehicle", "status", "updated_at"])
        # create status update entry
        DispatchStatusUpdate.objects.create(dispatch=dispatch, status="ASSIGNED", note="Assigned by admin", created_by=request.user)
        return Response(self.get_serializer(dispatch).data)

    @action(detail=True, methods=["post"], url_path="update-status", permission_classes=[permissions.IsAuthenticated, IsEmailVerified])
    def update_status(self, request, pk=None):
        """
        Agent or admin updates status. Payload: {"status":"PICKED_UP", "note":"...","location":"..."}
        """
        dispatch = self.get_object()
        status_value = request.data.get("status")
        note = request.data.get("note", "")
        location = request.data.get("location", "")
        if status_value not in dict(Dispatch._meta.get_field("status").choices):
            return Response({"detail": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)
        # Only allow assigned agent or admin to update
        user = request.user
        if not (user.is_staff or (dispatch.assigned_agent and dispatch.assigned_agent.user == user)):
            return Response({"detail": "Not permitted."}, status=status.HTTP_403_FORBIDDEN)
        # update dispatch times for pickup/delivered
        if status_value == "PICKED_UP":
            dispatch.pickup_time = timezone.now()
        if status_value == "DELIVERED":
            dispatch.delivery_time = timezone.now()
        dispatch.status = status_value
        dispatch.save(update_fields=["status", "pickup_time", "delivery_time", "updated_at"])
        # create status log
        su = DispatchStatusUpdate.objects.create(dispatch=dispatch, status=status_value, note=note, location=location, created_by=user)
        return Response(DispatchStatusUpdateSerializer(su).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="confirm-delivery", permission_classes=[permissions.IsAuthenticated, IsEmailVerified])
    def confirm_delivery(self, request, pk=None):
        """
        Agent posts proof of delivery (photo/signature URL) and receiver name.
        Payload: {"proof_of_delivery_url":"...", "receiver_name":"..."}
        """
        dispatch = self.get_object()
        user = request.user
        if not (user.is_staff or (dispatch.assigned_agent and dispatch.assigned_agent.user == user)):
            return Response({"detail": "Not permitted."}, status=status.HTTP_403_FORBIDDEN)
        proof = request.data.get("proof_of_delivery_url", "")
        receiver_name = request.data.get("receiver_name", "")
        dispatch.proof_of_delivery_url = proof
        dispatch.receiver_name = receiver_name
        dispatch.status = "DELIVERED"
        dispatch.delivery_time = timezone.now()
        dispatch.save(update_fields=["proof_of_delivery_url", "receiver_name", "status", "delivery_time", "updated_at"])
        DispatchStatusUpdate.objects.create(dispatch=dispatch, status="DELIVERED", note="Proof uploaded", created_by=user)
        return Response(self.get_serializer(dispatch).data)

    @action(detail=True, methods=["post"], url_path="set-cost", permission_classes=[permissions.IsAdminUser, IsEmailVerified])
    def set_cost(self, request, pk=None):
        dispatch = self.get_object()
        try:
            cost = float(request.data.get("cost"))
        except Exception:
            return Response({"detail": "Invalid cost"}, status=status.HTTP_400_BAD_REQUEST)
        dispatch.cost = cost
        dispatch.save(update_fields=["cost", "updated_at"])
        return Response(self.get_serializer(dispatch).data)


class DispatchStatusUpdateViewSet(viewsets.ModelViewSet):
    queryset = DispatchStatusUpdate.objects.select_related("created_by").all()
    serializer_class = DispatchStatusUpdateSerializer
    permission_classes = [IsStaffOrAgent, IsEmailVerified]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)
