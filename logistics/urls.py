# logistics/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    LogisticsAgentViewSet, VehicleViewSet, DispatchViewSet, DispatchStatusUpdateViewSet
)

router = DefaultRouter()
router.register(r'agents', LogisticsAgentViewSet, basename='logisticsagent')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'dispatches', DispatchViewSet, basename='dispatch')
router.register(r'dispatch-status-updates', DispatchStatusUpdateViewSet, basename='dispatchstatusupdate')

urlpatterns = router.urls
