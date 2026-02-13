import pytest
from rest_framework.test import APIRequestFactory
from django.core.cache import cache

from core.views import HomepageAPIView, CACHE_KEY
from products.models import Category, MenuItem


@pytest.mark.django_db
def test_homepage_view_caches_response():
    cache.delete(CACHE_KEY)
    Category.objects.create(name="Rice", slug="rice")
    MenuItem.objects.create(name="Jollof", slug="jollof", price=10, is_available=True)

    factory = APIRequestFactory()
    request = factory.get("/api/home/")
    response = HomepageAPIView.as_view()(request)
    assert response.status_code == 200
    assert cache.get(CACHE_KEY) is not None
