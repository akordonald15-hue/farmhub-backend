import pytest
from farmers.serializers import FarmerProductSerializer, SupplyRecordSerializer
from farmers.models import Farmer, FarmerProduct


@pytest.mark.django_db
def test_farmer_product_serializer_validation():
    farmer = Farmer.objects.create(contact_name="Farmer S")
    serializer = FarmerProductSerializer(data={"farmer": farmer.id, "title": "Test", "price_per_unit": -1, "quantity_available": 1})
    assert serializer.is_valid() is False
    assert "price_per_unit" in serializer.errors


@pytest.mark.django_db
def test_supply_record_serializer_sets_default_date():
    farmer = Farmer.objects.create(contact_name="Farmer S2")
    product = FarmerProduct.objects.create(farmer=farmer, title="Rice", price_per_unit=1, quantity_available=1)
    serializer = SupplyRecordSerializer(data={"farmer": farmer.id, "product": product.id, "quantity": 1, "unit": "kg"})
    assert serializer.is_valid() is True
    record = serializer.save()
    assert record.supply_date is not None
