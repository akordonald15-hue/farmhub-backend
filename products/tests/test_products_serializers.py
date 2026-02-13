import pytest
from products.serializers import MenuItemSerializer, CategorySerializer
from products.models import Category


@pytest.mark.django_db
def test_menu_item_serializer_validation():
    category = Category.objects.create(name="Wraps", slug="wraps")
    serializer = MenuItemSerializer(data={"category": category.id, "name": "A", "slug": "a", "price": 0})
    assert serializer.is_valid() is False


@pytest.mark.django_db
def test_category_serializer():
    category = Category.objects.create(name="Rice", slug="rice")
    data = CategorySerializer(category).data
    assert data["name"] == "Rice"
