# farmers/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.permissions import IsEmailVerified

from .models import Farmer, FarmerDocument, FarmerProduct, SupplyRecord
from .serializers import (
    FarmerSerializer,
    FarmerDocumentSerializer,
    FarmerProductSerializer,
    SupplyRecordSerializer,
)


# Simple custom permission: allow only admin/staff or owner (farmer) for unsafe methods
class IsAdminOrOwner(permissions.BasePermission):
    """
    Allow safe methods to anyone, but write methods only to staff or the farmer owner (if applicable).
    """
    def has_permission(self, request, view):
        # Allow listing and retrieving for authenticated users (or we can allow anon for list)
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Safe methods allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Staff can do anything
        if request.user.is_staff:
            return True
        # If Farmer has a linked user, allow owner
        if hasattr(obj, "user") and obj.user:
            return obj.user == request.user
        # For FarmerProduct or SupplyRecord, check farmer relation
        if hasattr(obj, "farmer") and obj.farmer and obj.farmer.user:
            return obj.farmer.user == request.user
        return False


class FarmerViewSet(viewsets.ModelViewSet):
    """
    Admins can create/update/verify farmers.
    Optionally, farmers who are linked to User accounts can update their profile.
    """
    queryset = Farmer.objects.all().select_related("user")
    serializer_class = FarmerSerializer
    permission_classes = [IsAdminOrOwner, IsEmailVerified]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("contact_name", "business_name", "phone", "state", "lga")
    ordering_fields = ("created_at", "business_name", "contact_name")

    def get_queryset(self):
        qs = super().get_queryset()
        # Optionally limit non-staff users to their own profile
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            # if user is linked to a farmer profile, show only that
            try:
                farmer_profile = self.request.user.farmer_profile
            except Exception:
                farmer_profile = None
            if farmer_profile:
                return qs.filter(pk=farmer_profile.pk)
        return qs

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser, IsEmailVerified])
    def verify(self, request, pk=None):
        farmer = self.get_object()
        status_value = request.data.get("status", "VERIFIED")
        note = request.data.get("note", "")
        if status_value not in dict(Farmer._meta.get_field("verified").choices):
            return Response({"detail": "Invalid verification status."}, status=status.HTTP_400_BAD_REQUEST)
        farmer.verified = status_value
        farmer.verification_note = note
        farmer.save(update_fields=["verified", "verification_note"])
        return Response(self.get_serializer(farmer).data)


class FarmerProductViewSet(viewsets.ModelViewSet):
    queryset = FarmerProduct.objects.select_related("farmer").all()
    serializer_class = FarmerProductSerializer
    permission_classes = [IsAdminOrOwner, IsEmailVerified]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("title", "category", "farmer__contact_name", "farmer__business_name")
    ordering_fields = ("created_at", "price_per_unit", "quantity_available")

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Non-staff users see only their farmer products if linked
        if user and user.is_authenticated and not user.is_staff:
            try:
                farmer_profile = user.farmer_profile
                return qs.filter(farmer=farmer_profile)
            except Exception:
                return qs.none()
        return qs

    def perform_create(self, serializer):
        """
        If the user is a farmer (linked), ensure created product is linked to that farmer.
        Admins can create with explicit farmer field.
        """
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            if hasattr(user, "farmer_profile"):
                serializer.save(farmer=user.farmer_profile)
                return
        # fallback to provided farmer (admin)
        serializer.save()


class SupplyRecordViewSet(viewsets.ModelViewSet):
    queryset = SupplyRecord.objects.select_related("farmer", "product").all()
    serializer_class = SupplyRecordSerializer
    permission_classes = [IsAdminOrOwner, IsEmailVerified]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("farmer__contact_name", "product__title", "reference_code")
    ordering_fields = ("supply_date", "created_at")

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            try:
                farmer_profile = user.farmer_profile
                return qs.filter(farmer=farmer_profile)
            except Exception:
                return qs.none()
        return qs

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser, IsEmailVerified])
    def update_status(self, request, pk=None):
        """
        Admin action to update supply status to APPROVED/REJECTED/COMPLETED.
        """
        supply = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(SupplyRecord.STATUS_CHOICES):
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        supply.status = new_status
        supply.quality_notes = request.data.get("quality_notes", supply.quality_notes)
        supply.received_by = request.data.get("received_by", supply.received_by)
        supply.save(update_fields=["status", "quality_notes", "received_by", "updated_at"])
        return Response(self.get_serializer(supply).data)


class FarmerDocumentViewSet(viewsets.ModelViewSet):
    queryset = FarmerDocument.objects.select_related("farmer").all()
    serializer_class = FarmerDocumentSerializer
    permission_classes = [IsAdminOrOwner, IsEmailVerified]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name", "farmer__contact_name", "farmer__business_name")
    ordering_fields = ("uploaded_at",)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated and not user.is_staff:
            try:
                farmer_profile = user.farmer_profile
                return qs.filter(farmer=farmer_profile)
            except Exception:
                return qs.none()
        return qs

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser, IsEmailVerified])
    def verify_document(self, request, pk=None):
        doc = self.get_object()
        doc.verified = bool(request.data.get("verified", True))
        doc.notes = request.data.get("notes", doc.notes)
        doc.save(update_fields=["verified", "notes"])
        return Response(self.get_serializer(doc).data)
