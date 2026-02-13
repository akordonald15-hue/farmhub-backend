from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from accounts.permissions import IsEmailVerified

from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsOwnerOrReadOnly

import logging
admin_logger = logging.getLogger('admin_actions')


class AdminThrottle(UserRateThrottle):
    rate = '50/hour'


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEmailVerified, IsOwnerOrReadOnly]

    # -----------------------------
    # Add request to serializer context
    # -----------------------------
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        serializer.save()  # ✅ Just save()

    # -----------------------------
    # List reviews with pagination support
    # Returns paginated response if enabled, otherwise standard list format
    # -----------------------------
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "results": serializer.data,  # ✅ Changed to "results"
            "count": queryset.count()
        })

    # -----------------------------
    # Admin: update review status
    # -----------------------------
    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAdminUser, IsEmailVerified],
        throttle_classes=[AdminThrottle]
    )
    def update_status(self, request, pk=None):
        review = self.get_object()
        old_status = review.status
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        review.status = new_status
        review.save()

        admin_logger.info(
            f"Admin {request.user.username} updated review {review.id} "
            f"status from '{old_status}' to '{new_status}'"
        )

        return Response({
            "message": "Review status updated successfully",
            "old_status": old_status,
            "new_status": new_status
        }, status=status.HTTP_200_OK)
