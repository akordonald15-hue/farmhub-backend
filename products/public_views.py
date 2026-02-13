# menu/views_public.py
from django.core.cache import cache
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import permissions
from .models import MenuItem
from .serializers import MenuItemSerializer
from core.responses import success_response  # adjust import path if project name differs

CACHE_KEY = "public_menu_list_v1"
CACHE_TTL = 300  # seconds

class PublicMenuViewSet(ReadOnlyModelViewSet):
    queryset = MenuItem.objects.filter(is_available=True).select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        cached = cache.get(CACHE_KEY)
        if cached:
            return success_response("Menu fetched (cached)", data=cached)

        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        data = serializer.data
        cache.set(CACHE_KEY, data, timeout=CACHE_TTL)
        return success_response("Menu fetched", data=data)
