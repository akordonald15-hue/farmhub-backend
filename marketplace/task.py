# marketplace/tasks.py
"""
Minimal Celery task to scan low stock and notify farmer/admin.
Requires Celery setup in the project. Safe to include even if Celery isn't used yet.
"""
try:
    from celery import shared_task
except ImportError:  # pragma: no cover - optional dependency
    def shared_task(func=None, **_kwargs):
        if func is None:
            def wrapper(f):
                return f
            return wrapper
        return func
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import Product

DEFAULT_THRESHOLD = getattr(settings, "MARKETPLACE_LOW_STOCK_THRESHOLD", 10)  # default units

@shared_task
def send_low_stock_alerts(threshold=None):
    """
    Find products with quantity <= threshold and send alerts to farmer email (if present).
    """
    thr = threshold or DEFAULT_THRESHOLD
    products = Product.objects.filter(quantity__lte=thr, is_active=True)
    alerts_sent = 0
    for p in products:
        farmer_email = p.farmer.email
        if farmer_email:
            subject = f"Low stock alert: {p.title}"
            message = f"Your product '{p.title}' has low stock ({p.quantity} {p.unit}). Please replenish."
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [farmer_email])
                alerts_sent += 1
            except Exception:
                # avoid task failing due to email config
                continue
    return {"checked": products.count(), "alerts_sent": alerts_sent, "checked_at": timezone.now().isoformat()}
