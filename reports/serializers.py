from rest_framework import serializers
from .models import GeneratedReport

# Read-only serializer for GeneratedReport (optional, for audit logs)
class GeneratedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedReport
        fields = [
            "id",
            "report_type",
            "generated_by",
            "generated_at",
            "parameters",
            "result_snapshot",
        ]
        read_only_fields = fields

# Read-only serializers for report responses
class UserReportSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField(allow_null=True)
    new_users = serializers.IntegerField()

class OrderReportSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField(allow_null=True)
    cancelled_orders = serializers.IntegerField(allow_null=True)
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

class PaymentReportSerializer(serializers.Serializer):
    successful = serializers.IntegerField(allow_null=True)
    failed = serializers.IntegerField(allow_null=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method_breakdown = serializers.DictField(child=serializers.IntegerField(), required=False)

class ReviewReportSerializer(serializers.Serializer):
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()

class DashboardSummarySerializer(serializers.Serializer):
    users = UserReportSerializer()
    orders = OrderReportSerializer()
    payments = PaymentReportSerializer()
    reviews = ReviewReportSerializer()
