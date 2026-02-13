from rest_framework.routers import DefaultRouter
from .views import (
    DashboardReportViewSet,
    UserReportViewSet,
    OrderReportViewSet,
    PaymentReportViewSet,
    ReviewReportViewSet,
)

router = DefaultRouter()
router.register(r"dashboard", DashboardReportViewSet, basename="reports-dashboard")
router.register(r"users", UserReportViewSet, basename="reports-users")
router.register(r"orders", OrderReportViewSet, basename="reports-orders")
router.register(r"payments", PaymentReportViewSet, basename="reports-payments")
router.register(r"reviews", ReviewReportViewSet, basename="reports-reviews")

urlpatterns = router.urls
