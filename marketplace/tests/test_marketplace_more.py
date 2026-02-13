import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from farmers.models import Farmer
from marketplace.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_marketplace_adjust_stock_insufficient(client):
    admin = User.objects.create_superuser(username="admin_stock", password="p", email="admin_stock@test.com")
    admin.is_verified = True
    admin.save(update_fields=["is_verified"])
    client.force_login(admin)

    farmer = Farmer.objects.create(contact_name="Farmer Stock")
    category = Category.objects.create(name="Veg4", slug="veg4")
    product = Product.objects.create(
        farmer=farmer,
        title="Tomato",
        slug="tomato",
        category=category,
        price="10.00",
        quantity="1.000",
        min_order="1.000",
    )
    r = client.post(
        f"/api/marketplace/products/{product.id}/adjust_stock/",
        data={"change_qty": "2", "change_type": "OUT"},
    )
    assert r.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_marketplace_inventory_requires_auth(client):
    user = User.objects.create_user(email="inv_user@example.com", password="StrongPass123", full_name="Inv User")
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    client.force_login(user)

    farmer = Farmer.objects.create(contact_name="Farmer Inv")
    category = Category.objects.create(name="Veg5", slug="veg5")
    product = Product.objects.create(
        farmer=farmer,
        title="Okra",
        slug="okra",
        category=category,
        price="10.00",
        quantity="1.000",
        min_order="1.000",
    )

    r = client.get(f"/api/marketplace/products/{product.id}/inventory/")
    assert r.status_code == status.HTTP_200_OK
