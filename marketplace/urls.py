# marketplace/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, ProductImageViewSet, InventoryRecordViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='marketplace-category')
router.register(r'products', ProductViewSet, basename='marketplace-product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'inventory-records', InventoryRecordViewSet, basename='inventory-record')

urlpatterns = router.urls
