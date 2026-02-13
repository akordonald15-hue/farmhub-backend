import requests
import hmac, hashlib
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from accounts.permissions import IsEmailVerified
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

from orders.models import Order
from core.logging_utils import log_event
from .serializers import (
    InitializePaymentSerializer,
    VerifyPaymentSerializer,
    PaystackWebhookSerializer,
    PaymentInitResponseSerializer,
    PaymentVerifyResponseSerializer
)


# ============================================================
# 1️⃣ INITIALIZE PAYMENT
# ============================================================
@extend_schema(
    request=InitializePaymentSerializer,
    responses={200: PaymentInitResponseSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def initialize_payment(request):

    serializer = InitializePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order_id = serializer.validated_data["order_id"]
    callback_url = serializer.validated_data.get("callback_url")

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=404)

    if order.paid:
        return Response({"detail": "Order already paid"}, status=400)

    if not order.items.exists() or order.total_price <= 0:
        return Response({"detail": "Invalid order"}, status=400)

    initialize_url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"

    payload = {
        "email": request.user.email,
        "amount": int(order.total_price * 100),
        "currency": "NGN",
        "reference": f"order-{order.id}",
        "metadata": {"order_id": order.id},
        "callback_url": callback_url,
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(initialize_url, json=payload, headers=headers)

    if response.status_code not in [200, 201]:
        return Response(
            {"detail": "Paystack init failed", "paystack": response.json()},
            status=502
        )

    paystack_data = response.json()

    # store reference
    order.paystack_reference = paystack_data["data"]["reference"]
    order.save()

    return Response(paystack_data)



# ============================================================
# 2️⃣ VERIFY PAYMENT
# ============================================================
@extend_schema(
    request=VerifyPaymentSerializer,
    responses={200: PaymentVerifyResponseSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def verify_payment(request):

    serializer = VerifyPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reference = serializer.validated_data["reference"]

    verify_url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.get(verify_url, headers=headers)

    if response.status_code != 200:
        return Response({"detail": "Verification failed"}, status=502)

    result = response.json()
    data = result.get("data", {})

    if data.get("status") != "success":
        return Response({"detail": "Payment not successful"}, status=400)

    order_id = data.get("metadata", {}).get("order_id")

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"detail": "Order not found"}, status=404)

    order.paid = True
    order.save()

    return Response({"detail": "Payment verified", "status": "paid"})


# ============================================================
# 3️⃣ PAYSTACK WEBHOOK (SERVER CONFIRMATION)
# ============================================================
@extend_schema(
    request=PaystackWebhookSerializer,
    responses={200: PaystackWebhookSerializer}
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def paystack_webhook(request):

    signature = request.headers.get("x-paystack-signature")

    if not signature:
        log_event("order_events", request, "paystack_webhook", "failure")
        return Response({"detail": "Missing signature"}, status=400)

    body = request.body
    secret = settings.PAYSTACK_SECRET_KEY.encode()
    expected = hmac.new(secret, body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(expected, signature):
        log_event("order_events", request, "paystack_webhook", "failure")
        return Response({"detail": "Invalid signature"}, status=403)

    event = request.data.get("event")
    data = request.data.get("data", {})

    if event == "charge.success":
        reference = data.get("reference")
        order_id = data.get("metadata", {}).get("order_id")

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.paid = True
                order.paystack_reference = reference
                order.save()
            except Order.DoesNotExist:
                pass

    log_event("order_events", request, "paystack_webhook", "success")
    return Response({"status": "ok"})
