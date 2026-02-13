import pytest
from menu.models import Category, MenuItem

@pytest.mark.django_db
def test_menuitem_and_category():
    c = Category.objects.create(name="Burgers", slug="burgers")
    item = MenuItem.objects.create(
        category=c, name="Beef Burger", slug="beef-burger",
        description="Test", price=1500.00, is_available=True
    )
    assert item.category == c
    assert str(item) == "Beef Burger"
