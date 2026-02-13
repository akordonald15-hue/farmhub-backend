# marketplace/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.permissions import IsEmailVerified

from .models import Category, Product, ProductImage, InventoryRecord
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductImageSerializer, InventoryRecordSerializer
)
from .permissions import IsAdminOrReadOnly, IsFarmerOrAdmin
from .filters import ProductFilter
from .services import adjust_product_stock

try:
    from django_filters.rest_framework import DjangoFilterBackend
except ImportError:  # pragma: no cover - optional dependency for tests
    DjangoFilterBackend = None


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly, IsEmailVerified]
    lookup_field = 'id'


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('farmer', 'category').prefetch_related('images').all()
    filter_backends = [backend for backend in (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter) if backend]
    filterset_class = ProductFilter
    search_fields = ('title', 'description', 'farmer__contact_name', 'farmer__business_name')
    ordering_fields = ('price', 'quantity', 'created_at')
    permission_classes = [IsFarmerOrAdmin, IsEmailVerified]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ProductDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def perform_create(self, serializer):
        user = self.request.user
        # Non-staff users with linked farmer_profile automatically set the farmer field
        if user and user.is_authenticated and not user.is_staff and hasattr(user, 'farmer_profile'):
            serializer.save(farmer=user.farmer_profile, created_by=user)
            return
        serializer.save(created_by=user)

    @action(detail=True, methods=['post'], permission_classes=[IsFarmerOrAdmin, IsEmailVerified])
    def adjust_stock(self, request, pk=None):
        """
        Adjust stock for a product (IN or OUT).
        payload: {"change_qty": "10.5", "change_type": "IN", "note": "..."}
        """
        product = self.get_object()
        change_qty = request.data.get('change_qty')
        change_type = request.data.get('change_type', 'ADJUST')
        note = request.data.get('note', "")
        try:
            change_qty = float(change_qty)
        except Exception:
            return Response({"detail": "Invalid change_qty"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            updated = adjust_product_stock(product.id, abs(change_qty), change_type=change_type, performed_by=request.user, note=note)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductDetailSerializer(updated, context={'request': request}).data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsEmailVerified])
    def inventory(self, request, pk=None):
        product = self.get_object()
        records = product.inventory_records.all()
        page = self.paginate_queryset(records)
        if page is not None:
            serializer = InventoryRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = InventoryRecordSerializer(records, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsFarmerOrAdmin, IsEmailVerified]


class InventoryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryRecord.objects.select_related('product', 'performed_by').all()
    serializer_class = InventoryRecordSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsEmailVerified]
