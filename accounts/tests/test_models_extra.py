import pytest
from django.contrib.auth import get_user_model

from accounts.models import EmailVerification, CustomerProfile, FarmerProfile, VendorProfile, LogisticsAgentProfile

User = get_user_model()


@pytest.mark.django_db
def test_create_user_requires_email_or_username():
    with pytest.raises(ValueError):
        User.objects.create_user(password="StrongPass123")


@pytest.mark.django_db
def test_user_natural_key():
    user = User.objects.create_user(email="natural@example.com", password="StrongPass123", full_name="Natural User")
    assert user.natural_key() == ("natural@example.com",)


@pytest.mark.django_db
def test_email_verification_str():
    user = User.objects.create_user(email="verify_str@example.com", password="StrongPass123", full_name="Verify Str")
    verification = EmailVerification.objects.get(user=user)
    assert str(verification) == f"EmailVerification({user.email})"


@pytest.mark.django_db
def test_profile_strs():
    user1 = User.objects.create_user(email="cust@example.com", password="StrongPass123", full_name="Cust User", role="customer")
    user2 = User.objects.create_user(email="farm@example.com", password="StrongPass123", full_name="Farm User", role="farmer")
    user3 = User.objects.create_user(email="vendor@example.com", password="StrongPass123", full_name="Vendor User", role="vendor")
    user4 = User.objects.create_user(email="logi@example.com", password="StrongPass123", full_name="Logi User", role="logistics")

    c = CustomerProfile.objects.get(user=user1)
    f = FarmerProfile.objects.get(user=user2)
    v = VendorProfile.objects.get(user=user3)
    l = LogisticsAgentProfile.objects.get(user=user4)

    assert str(c) == f"CustomerProfile({user1.email})"
    assert str(f) == f"FarmerProfile({user2.email})"
    assert str(v) == f"VendorProfile({user3.email})"
    assert str(l) == f"LogisticsAgentProfile({user4.email})"
