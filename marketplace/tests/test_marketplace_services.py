import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from marketplace.models import Category, Product
from marketplace.services import adjust_product_stock
from farmers.models import Farmer

User = get_user_model()


@pytest.mark.django_db
def test_adjust_product_stock_in_and_out():
    farmer = Farmer.objects.create(contact_name="Farmer M")
    category = Category.objects.create(name="Cat", slug="cat")
    product = Product.objects.create(
        farmer=farmer,
        title="Tomato",
        slug="tomato",
        category=category,
        price=Decimal("10.00"),
        quantity=Decimal("5.000"),
        min_order=Decimal("1.000"),
    )

    adjust_product_stock(product.id, 2, change_type="IN")
    product.refresh_from_db()
    assert product.quantity == Decimal("7.000")

    adjust_product_stock(product.id, 1, change_type="OUT")
    product.refresh_from_db()
    assert product.quantity == Decimal("6.000")

    with pytest.raises(ValueError):
        adjust_product_stock(product.id, 100, change_type="OUT")
