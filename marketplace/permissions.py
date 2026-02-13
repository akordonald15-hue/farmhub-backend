# marketplace/permissions.py
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Unsafe methods only allowed for staff users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsFarmerOrAdmin(permissions.BasePermission):
    """
    Allow actions to staff or to the farmer who owns the product.
    """
    def has_object_permission(self, request, view, obj):
        # Safe methods allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        # Staff allowed
        if request.user and request.user.is_staff:
            return True
        # For Product objects
        if hasattr(obj, "farmer") and obj.farmer and hasattr(request.user, "farmer_profile"):
            return obj.farmer == request.user.farmer_profile
        return False
