import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from farmers.models import Farmer, FarmerProduct, SupplyRecord

User = get_user_model()


@pytest.mark.django_db
def test_farmers_list_and_verify_action(client):
    admin = User.objects.create_superuser(username="admin_f", password="p", email="admin_f@test.com")
    client.force_login(admin)

    farmer = Farmer.objects.create(contact_name="Farmer One")
    r_list = client.get("/api/farmers/farmers/")
    assert r_list.status_code == status.HTTP_200_OK

    r_verify = client.post(f"/api/farmers/farmers/{farmer.id}/verify/", data={"status": "VERIFIED"})
    assert r_verify.status_code == status.HTTP_200_OK

    r_invalid = client.post(f"/api/farmers/farmers/{farmer.id}/verify/", data={"status": "BAD"})
    assert r_invalid.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_supply_record_update_status_invalid(client):
    admin = User.objects.create_superuser(username="admin_s", password="p", email="admin_s@test.com")
    client.force_login(admin)

    farmer = Farmer.objects.create(contact_name="Farmer Two")
    product = FarmerProduct.objects.create(farmer=farmer, title="Maize", price_per_unit=10, quantity_available=1)
    supply = SupplyRecord.objects.create(farmer=farmer, product=product, quantity=1)

    r = client.post(f"/api/farmers/supply-records/{supply.id}/update_status/", data={"status": "BAD"})
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_farmer_products_and_docs_list(client):
    admin = User.objects.create_superuser(username="admin_f2", password="p", email="admin_f2@test.com")
    client.force_login(admin)

    farmer = Farmer.objects.create(contact_name="Farmer Docs")
    r_products = client.get("/api/farmers/farmer-products/")
    assert r_products.status_code == status.HTTP_200_OK

    r_docs = client.get("/api/farmers/farmer-docs/")
    assert r_docs.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_farmer_list_for_non_staff_user(client):
    user = User.objects.create_user(email="farmer_user@example.com", password="p", full_name="Farmer User", role="farmer")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)
    r = client.get("/api/farmers/farmers/")
    assert r.status_code == status.HTTP_200_OK
