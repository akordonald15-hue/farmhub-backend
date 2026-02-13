from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from accounts.permissions import IsEmailVerified
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError

from . import services
from .serializers import (
    UserReportSerializer,
    OrderReportSerializer,
    PaymentReportSerializer,
    ReviewReportSerializer,
    DashboardSummarySerializer,
)
def parse_date_range(request):
    now = timezone.now()
    period = request.query_params.get("period", "custom")
    start = request.query_params.get("start_date")
    end = request.query_params.get("end_date")

    if period == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    elif period == "weekly":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    elif period == "monthly":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    elif period == "custom":
        if not start or not end:
            raise ValidationError("Custom period requires start_date and end_date.")
        start_date = timezone.make_aware(timezone.datetime.fromisoformat(start))
        end_date = timezone.make_aware(timezone.datetime.fromisoformat(end))

    else:
        raise ValidationError("Invalid period. Use daily, weekly, monthly, or custom.")

    return start_date, end_date
class DashboardReportViewSet(ViewSet):
    permission_classes = [IsAdminUser, IsEmailVerified]

    def list(self, request):
        start_date, end_date = parse_date_range(request)
        data = services.get_dashboard_summary(start_date, end_date)
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)
class UserReportViewSet(ViewSet):
    permission_classes = [IsAdminUser, IsEmailVerified]

    def list(self, request):
        start_date, end_date = parse_date_range(request)
        data = services.get_user_report(start_date, end_date)
        serializer = UserReportSerializer(data)
        return Response(serializer.data)
class OrderReportViewSet(ViewSet):
    permission_classes = [IsAdminUser, IsEmailVerified]

    def list(self, request):
        start_date, end_date = parse_date_range(request)
        data = services.get_order_report(start_date, end_date)
        serializer = OrderReportSerializer(data)
        return Response(serializer.data)
class PaymentReportViewSet(ViewSet):
    permission_classes = [IsAdminUser, IsEmailVerified]

    def list(self, request):
        start_date, end_date = parse_date_range(request)
        data = services.get_payment_report(start_date, end_date)
        serializer = PaymentReportSerializer(data)
        return Response(serializer.data)
class ReviewReportViewSet(ViewSet):
    permission_classes = [IsAdminUser, IsEmailVerified]

    def list(self, request):
        start_date, end_date = parse_date_range(request)
        data = services.get_review_report(start_date, end_date)
        serializer = ReviewReportSerializer(data)
        return Response(serializer.data)
