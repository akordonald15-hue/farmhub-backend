# farmers/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FarmerViewSet,
    FarmerProductViewSet,
    SupplyRecordViewSet,
    FarmerDocumentViewSet,
)

router = DefaultRouter()
router.register(r'farmers', FarmerViewSet, basename='farmer')
router.register(r'farmer-products', FarmerProductViewSet, basename='farmerproduct')
router.register(r'supply-records', SupplyRecordViewSet, basename='supplyrecord')
router.register(r'farmer-docs', FarmerDocumentViewSet, basename='farmerdocument')

urlpatterns = [
    path("", include(router.urls)),  # include all viewsets under this app
]
