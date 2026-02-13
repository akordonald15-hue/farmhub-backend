import pytest
from marketplace.filters import ProductFilter
from marketplace.models import Product, Category
from farmers.models import Farmer


@pytest.mark.django_db
def test_product_filter_search():
    farmer = Farmer.objects.create(contact_name="Farmer F")
    category = Category.objects.create(name="Cat", slug="cat")
    product = Product.objects.create(
        farmer=farmer,
        title="Apple",
        slug="apple",
        category=category,
        price="10.00",
        quantity="5.000",
        min_order="1.000",
    )
    f = ProductFilter(data={"q": "Apple"}, queryset=Product.objects.all())
    assert f.qs.count() == 1
