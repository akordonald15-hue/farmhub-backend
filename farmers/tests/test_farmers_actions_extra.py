import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from farmers.models import Farmer, FarmerDocument, FarmerProduct, SupplyRecord

User = get_user_model()


@pytest.mark.django_db
def test_farmer_owner_can_update_profile(client):
    user = User.objects.create_user(
        email="farmer_owner@example.com",
        password="StrongPass123",
        full_name="Farmer Owner",
        role="farmer",
    )
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    farmer = Farmer.objects.create(contact_name="Old Name", user=user)

    client.force_login(user)
    r = client.patch(f"/api/farmers/farmers/{farmer.id}/", data={"contact_name": "New Name"})
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_verify_farmer_document(client):
    admin = User.objects.create_superuser(username="admin_doc", password="p", email="admin_doc@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    farmer = Farmer.objects.create(contact_name="Doc Farmer")
    doc = FarmerDocument.objects.create(farmer=farmer, name="NIN", file_url="http://example.com/nin.png")

    client.force_login(admin)
    r = client.post(f"/api/farmers/farmer-docs/{doc.id}/verify_document/", data={"verified": False, "notes": "Bad"})
    assert r.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_admin_can_update_supply_status_valid(client):
    admin = User.objects.create_superuser(username="admin_supply", password="p", email="admin_supply@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    farmer = Farmer.objects.create(contact_name="Supply Farmer")
    product = FarmerProduct.objects.create(farmer=farmer, title="Maize", price_per_unit=10, quantity_available=1)
    supply = SupplyRecord.objects.create(farmer=farmer, product=product, quantity=1)

    client.force_login(admin)
    r = client.post(
        f"/api/farmers/supply-records/{supply.id}/update_status/",
        data={"status": "APPROVED", "quality_notes": "ok"},
    )
    assert r.status_code == status.HTTP_200_OK
