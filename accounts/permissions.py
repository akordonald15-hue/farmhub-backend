from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    """
    Allows access only to users with verified email.
    If the request is unauthenticated, do not block (so public endpoints can work
    alongside AllowAny/IsAuthenticatedOrReadOnly).
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True
        return getattr(user, "is_verified", False) is True
