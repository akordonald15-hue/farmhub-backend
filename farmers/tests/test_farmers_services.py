import pytest
from django.core.exceptions import ValidationError

from farmers.models import Farmer, FarmerProduct
from farmers import services


@pytest.mark.django_db
def test_reserve_and_release_stock():
    farmer = Farmer.objects.create(contact_name="Farmer Service")
    product = FarmerProduct.objects.create(
        farmer=farmer,
        title="Maize",
        price_per_unit=10,
        quantity_available=5,
    )

    services.reserve_product_stock(product.id, 2)
    product.refresh_from_db()
    assert float(product.quantity_available) == 3.0

    services.release_product_stock(product.id, 2)
    product.refresh_from_db()
    assert float(product.quantity_available) == 5.0


@pytest.mark.django_db
def test_reserve_bulk_stock_errors():
    farmer = Farmer.objects.create(contact_name="Farmer Bulk")
    product = FarmerProduct.objects.create(
        farmer=farmer,
        title="Rice",
        price_per_unit=10,
        quantity_available=1,
    )
    with pytest.raises(ValidationError):
        services.reserve_bulk_stock([])
    with pytest.raises(ValidationError):
        services.reserve_bulk_stock([{"product_id": product.id, "quantity": 2}])
