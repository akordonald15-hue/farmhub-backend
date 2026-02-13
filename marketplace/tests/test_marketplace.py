import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from farmers.models import Farmer
from marketplace.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_marketplace_category_list_and_create(client):
    r_list = client.get("/api/marketplace/categories/")
    assert r_list.status_code == status.HTTP_200_OK

    admin = User.objects.create_superuser(username="admin_m", password="p", email="admin_m@test.com")
    client.force_login(admin)
    r_create = client.post("/api/marketplace/categories/", data={"name": "Grains", "slug": "grains"})
    assert r_create.status_code in (200, 201)


@pytest.mark.django_db
def test_marketplace_product_list_and_create(client):
    r_list = client.get("/api/marketplace/products/")
    assert r_list.status_code == status.HTTP_200_OK

    admin = User.objects.create_superuser(username="admin_p", password="p", email="admin_p@test.com")
    client.force_login(admin)
    farmer = Farmer.objects.create(contact_name="Farmer Joe")

    payload = {
        "farmer": str(farmer.id),
        "title": "Maize",
        "slug": "maize",
        "price": "10.00",
        "quantity": "5.000",
        "min_order": "1.000",
    }
    r_create = client.post("/api/marketplace/products/", data=payload)
    assert r_create.status_code in (200, 201)


@pytest.mark.django_db
def test_marketplace_adjust_stock_invalid_change_qty(client):
    admin = User.objects.create_superuser(username="admin_adj", password="p", email="admin_adj@test.com")
    client.force_login(admin)
    farmer = Farmer.objects.create(contact_name="Farmer A")
    category = Category.objects.create(name="Veg3", slug="veg3")
    product = Product.objects.create(
        farmer=farmer,
        title="Pepper3",
        slug="pepper3",
        category=category,
        price="10.00",
        quantity="5.000",
        min_order="1.000",
    )
    r = client.post(f"/api/marketplace/products/{product.id}/adjust_stock/", data={"change_qty": "bad"})
    assert r.status_code == status.HTTP_400_BAD_REQUEST

    r2 = client.post(f"/api/marketplace/products/{product.id}/adjust_stock/", data={"change_qty": "1", "change_type": "IN"})
    assert r2.status_code == status.HTTP_200_OK

    r3 = client.get(f"/api/marketplace/products/{product.id}/inventory/")
    assert r3.status_code == status.HTTP_200_OK
