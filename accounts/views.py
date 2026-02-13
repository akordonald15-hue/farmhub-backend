from rest_framework import generics, status, permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import PermissionDenied
from django.core.mail import send_mail
from rest_framework.throttling import UserRateThrottle, SimpleRateThrottle
from django.conf import settings

import logging

from core.logging_utils import log_event
from .models import (
    EmailVerification,
    CustomerProfile,
    FarmerProfile,
    VendorProfile,
    LogisticsAgentProfile,
)
from .serializers import (
    UserSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegistrationSerializer,
    EmailVerificationSerializer,
    ResendOTPSerializer,
    RefreshTokenSerializer,
)
from .permissions import IsEmailVerified

from orders.models import Order
from orders.serializers import OrderSerializer

User = get_user_model()

admin_logger = logging.getLogger('admin_actions')


class AdminThrottle(UserRateThrottle):
    rate = '30/hour'


class ResendOTPThrottle(SimpleRateThrottle):
    scope = "resend_otp"
    rate = "3/min"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if not email:
            return None
        ident = email.lower().strip()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginThrottle(SimpleRateThrottle):
    scope = "login"
    rate = "40/hour"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if not email:
            return None
        ident = email.lower().strip()
        return self.cache_format % {"scope": self.scope, "ident": ident}


class VerifyOTPThrottle(SimpleRateThrottle):
    scope = "verify_otp"
    rate = "40/hour"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if not email:
            return None
        ident = email.lower().strip()
        return self.cache_format % {"scope": self.scope, "ident": ident}


OTP_MAX_ATTEMPTS = 5


class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not getattr(self.user, "is_verified", False):
            raise PermissionDenied("Email not verified")
        return data


class VerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = VerifiedTokenObtainPairSerializer
    permission_classes = [AllowAny]


class VerifiedTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh")
        token = RefreshToken(refresh_token)
        user_id = token.get("user_id")
        user = User.objects.filter(id=user_id).first()
        if not user or not user.is_verified:
            raise PermissionDenied("Email not verified")

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# -------------------------------------------
# Order List (Admin / Tests)
# -------------------------------------------
class OrderListAPIView(ListAPIView):
    """
    Admin endpoint to view all orders.
    Only accessible to staff/admin users.
    """
    queryset = Order.objects.select_related('user').prefetch_related('items__menu_item')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser, IsEmailVerified]
    throttle_classes = [AdminThrottle]


# -------------------------------------------
# Register View
# -------------------------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            log_event("auth_events", request, "register", "failure")
            raise
        user = serializer.save()
        log_event("auth_events", request, "register", "success", user=user)

        # Signals will create EmailVerification and role-specific profile
        # Attempt to send OTP email
        try:
            verification = EmailVerification.objects.get(user=user)
            if verification.is_verified:
                verification.is_verified = False
                verification.save(update_fields=["is_verified"])

            verification.generate_otp()
            
            send_mail(
                subject="Your Farmhub Verification Code",
                message=f"Your verification code is: {verification.otp}\n\nDo not share this code with anyone.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=False,
            )
            log_event("auth_events", request, "otp_send", "success", user=user)
            admin_logger.info(f"OTP sent to user {user.id}: {user.email}")
        except EmailVerification.DoesNotExist:
            admin_logger.error(f"EmailVerification not created for user {user.id}")
            log_event("auth_events", request, "otp_send", "failure", user=user)
        except Exception as e:
            admin_logger.warning(f"Email send failed for user {user.id}: {str(e)}")
            log_event("auth_events", request, "otp_send", "failure", user=user)

        return Response({
            "message": "Registration successful. Please verify your email.",
            "user": UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


# -------------------------------------------
# Verify Email View
# -------------------------------------------
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [VerifyOTPThrottle]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
        except User.DoesNotExist:
            admin_logger.warning(f"Verification attempt for non-existent user: {email}")
            log_event("auth_events", request, "otp_verify", "failure")
            return Response({"error": "Invalid email or user not found."}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerification.DoesNotExist:
            admin_logger.warning(f"Verification record missing for user: {email}")
            log_event("auth_events", request, "otp_verify", "failure", user=user if "user" in locals() else None)
            return Response({"error": "Verification record not found."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.is_verified or user.is_verified:
            log_event("auth_events", request, "otp_verify", "failure", user=user)
            return Response({"error": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        if not verification.otp or verification.is_otp_expired():
            verification.invalidate_otp()
            admin_logger.warning(f"Expired OTP attempt for user: {email}")
            log_event("auth_events", request, "otp_verify", "failure", user=user, extra={"reason": "expired"})
            return Response({"error": "OTP expired. Please request a new OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.otp_attempts >= OTP_MAX_ATTEMPTS:
            verification.invalidate_otp()
            admin_logger.warning(f"OTP attempt limit reached for user: {email}")
            log_event("auth_events", request, "otp_lockout", "failure", user=user)
            return Response({"error": "OTP invalidated. Please request a new OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if verification.otp != otp:
            attempts = verification.increment_attempts()
            admin_logger.warning(f"Invalid OTP attempt for user: {email}")
            if attempts >= OTP_MAX_ATTEMPTS:
                verification.invalidate_otp()
                log_event("auth_events", request, "otp_lockout", "failure", user=user)
                return Response({"error": "OTP invalidated. Please request a new OTP."}, status=status.HTTP_400_BAD_REQUEST)
            log_event("auth_events", request, "otp_verify", "failure", user=user, extra={"reason": "invalid"})
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        verification.mark_verified()
        admin_logger.info(f"User {user.id} email verified: {email}")
        log_event("auth_events", request, "otp_verify", "success", user=user)
        return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)


# -------------------------------------------
# Resend OTP View
# -------------------------------------------
class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendOTPThrottle]
    serializer_class = ResendOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
        except User.DoesNotExist:
            admin_logger.warning(f"Resend OTP for non-existent user: {email}")
            log_event("auth_events", request, "otp_resend", "failure")
            return Response({"error": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)
        except EmailVerification.DoesNotExist:
            admin_logger.warning(f"Resend OTP missing verification record: {email}")
            log_event("auth_events", request, "otp_resend", "failure", user=user if "user" in locals() else None)
            return Response({"error": "Verification record not found."}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_verified or verification.is_verified:
            log_event("auth_events", request, "otp_resend", "failure", user=user)
            return Response({"error": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        verification.generate_otp()

        try:
            send_mail(
                subject="Your Farmhub Verification Code",
                message=f"Your verification code is: {verification.otp}\n\nDo not share this code with anyone.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=False,
            )
            admin_logger.info(f"OTP resent to user {user.id}: {user.email}")
            log_event("auth_events", request, "otp_resend", "success", user=user)
        except Exception as e:
            admin_logger.warning(f"OTP resend email failed for user {user.id}: {str(e)}")
            log_event("auth_events", request, "otp_resend", "failure", user=user)

        return Response({"message": "OTP resent successfully"}, status=status.HTTP_200_OK)


# -------------------------------------------
# Login View
# -------------------------------------------
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        password = serializer.validated_data['password']

        if not email and username:
            user_by_username = User.objects.filter(username=username).first()
            if not user_by_username:
                admin_logger.warning(f"Failed login attempt for username: {username}")
                log_event("auth_events", request, "login", "failure")
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            email = user_by_username.email

        user = authenticate(email=email, password=password)

        if not user:
            admin_logger.warning(f"Failed login attempt for email: {email}")
            log_event("auth_events", request, "login", "failure")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Require email verification
        if not user.is_verified:
            admin_logger.warning(f"Login blocked: email not verified for {email}")
            log_event("auth_events", request, "login", "blocked", user=user)
            return Response({"error": "Email not verified"}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        admin_logger.info(f"User {user.id} logged in successfully")
        log_event("auth_events", request, "login", "success", user=user)

        return Response({
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)


# -------------------------------------------
# Refresh Token View
# -------------------------------------------
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RefreshTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh_token']

        try:
            token = RefreshToken(refresh_token)
            user_id = token.get("user_id")
            user = User.objects.filter(id=user_id).first()
            if not user or not user.is_verified:
                log_event("auth_events", request, "token_refresh", "failure", user=user)
                raise PermissionDenied("Email not verified")
            admin_logger.info(f"Token refreshed successfully")
            log_event("auth_events", request, "token_refresh", "success", user=user)
            return Response({"access": str(token.access_token)}, status=status.HTTP_200_OK)
        except PermissionDenied:
            raise
        except Exception as e:
            admin_logger.warning(f"Invalid token refresh attempt: {str(e)}")
            log_event("auth_events", request, "token_refresh", "failure")
            return Response({"detail": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)


# -------------------------------------------
# Current User View
# -------------------------------------------
class CurrentUserView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get_object(self):
        return self.request.user


# -------------------------------------------
# Logout View
# -------------------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    serializer_class = LogoutSerializer

    def post(self, request):
        admin_logger.info(f"User {request.user.id} logged out")
        log_event("auth_events", request, "logout", "success", user=request.user)
        return Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)
# ...existing code...
