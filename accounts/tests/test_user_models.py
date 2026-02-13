import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_create_user():
    u = User.objects.create_user(username="donald", password="p")
    assert u.username == "donald"
    assert u.is_active


@pytest.mark.django_db
def test_role_profiles_created():
    farmer = User.objects.create_user(email="farmer@example.com", password="p", full_name="Farmer", role="farmer")
    vendor = User.objects.create_user(email="vendor@example.com", password="p", full_name="Vendor", role="vendor")
    logistics = User.objects.create_user(email="log@example.com", password="p", full_name="Log", role="logistics")

    assert hasattr(farmer, "farmerprofile")
    assert hasattr(vendor, "vendorprofile")
    assert hasattr(logistics, "logisticsagentprofile")
