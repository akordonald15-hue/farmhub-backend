# marketplace/filters.py
from .models import Product, Category

try:
    import django_filters
except ImportError:  # pragma: no cover - optional dependency for tests
    django_filters = None


if django_filters:
    class ProductFilter(django_filters.FilterSet):
        min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
        max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
        category = django_filters.UUIDFilter(field_name="category__id")
        farmer = django_filters.UUIDFilter(field_name="farmer__id")
        q = django_filters.CharFilter(method="search_filter")

        class Meta:
            model = Product
            fields = ["category", "farmer", "is_active", "featured"]

        def search_filter(self, queryset, name, value):
            return queryset.filter(title__icontains=value) | queryset.filter(description__icontains=value)
else:
    ProductFilter = None
