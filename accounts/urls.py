# ...existing code...
from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailView,
    ResendOTPView,
    CurrentUserView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    OrderListAPIView,
    VerifiedTokenObtainPairView,
    VerifiedTokenRefreshView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),

    # custom login (uses authenticate + EmailVerification)
    path("login/", LoginView.as_view(), name="login"),

    # standard simplejwt endpoints with verified check
    path("token/", VerifiedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", VerifiedTokenRefreshView.as_view(), name="token_refresh"),

    # custom refresh endpoint (keeps existing custom behaviour)
    path("refresh-token/", RefreshTokenView.as_view(), name="refresh-token"),

    # logout and current user
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current_user"),

    # admin/test endpoint
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
]
# ...existing code...
