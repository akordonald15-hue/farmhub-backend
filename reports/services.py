from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from accounts.models import User
from orders.models import Order
from reviews.models import Review


def get_user_report(start_date, end_date):
    qs = User.objects.filter(date_joined__gte=start_date, date_joined__lte=end_date)
    total_users = qs.count()
    verified_users = qs.filter(is_active=True, is_verified=True).count() if hasattr(User, 'is_verified') else None
    new_users = total_users
    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "new_users": new_users,
    }


def get_order_report(start_date, end_date):
    qs = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    total_orders = qs.count()
    completed_orders = qs.filter(status="DELIVERED").count() if hasattr(Order, 'status') else None
    cancelled_orders = qs.filter(status="CANCELLED").count() if hasattr(Order, 'status') else None
    revenue = qs.aggregate(total=Sum('total_price'))["total"] or 0
    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "revenue": revenue,
    }


def get_payment_report(start_date, end_date):
    try:
        from payments.models import Payment
    except Exception:
        return {
            "successful": 0,
            "failed": 0,
            "total_amount": 0,
            "method_breakdown": {},
        }
    qs = Payment.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    successful = qs.filter(status="successful").count() if hasattr(Payment, 'status') else None
    failed = qs.filter(status="failed").count() if hasattr(Payment, 'status') else None
    total_amount = qs.aggregate(total=Sum('amount'))["total"] or 0
    # Payment method breakdown (if field exists)
    method_breakdown = {}
    if hasattr(Payment, 'method'):
        method_breakdown = dict(qs.values_list('method').annotate(count=Count('id')))
    return {
        "successful": successful,
        "failed": failed,
        "total_amount": total_amount,
        "method_breakdown": method_breakdown,
    }


def get_review_report(start_date, end_date):
    qs = Review.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    total_reviews = qs.count()
    avg_rating = qs.aggregate(avg=Avg('rating'))["avg"] or 0
    return {
        "total_reviews": total_reviews,
        "average_rating": avg_rating,
    }


def get_dashboard_summary(start_date, end_date):
    """
    Returns a summary of all report types for dashboard view.
    """
    return {
        "users": get_user_report(start_date, end_date),
        "orders": get_order_report(start_date, end_date),
        "payments": get_payment_report(start_date, end_date),
        "reviews": get_review_report(start_date, end_date),
    }
