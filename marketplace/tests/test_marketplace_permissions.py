import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from farmers.models import Farmer
from marketplace.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_non_admin_cannot_create_category(client):
    user = User.objects.create_user(email="cat@example.com", password="p", full_name="Cat")
    client.force_login(user)
    r = client.post("/api/marketplace/categories/", data={"name": "Fruits", "slug": "fruits"})
    assert r.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_non_admin_cannot_update_product(client):
    admin = User.objects.create_superuser(username="admin_m2", password="p", email="admin_m2@test.com")
    farmer = Farmer.objects.create(contact_name="Farmer P")
    category = Category.objects.create(name="Veg", slug="veg")
    product = Product.objects.create(
        farmer=farmer,
        title="Pepper",
        slug="pepper",
        category=category,
        price="10.00",
        quantity="5.000",
        min_order="1.000",
    )

    user = User.objects.create_user(email="user_p@example.com", password="p", full_name="User P")
    client.force_login(user)
    r = client.patch(f"/api/marketplace/products/{product.id}/", data={"title": "New"})
    assert r.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
def test_is_farmer_or_admin_allows_staff(client):
    admin = User.objects.create_superuser(username="admin_p2", password="p", email="admin_p2@test.com")
    farmer = Farmer.objects.create(contact_name="Farmer P2")
    category = Category.objects.create(name="Veg2", slug="veg2")
    product = Product.objects.create(
        farmer=farmer,
        title="Pepper2",
        slug="pepper2",
        category=category,
        price="10.00",
        quantity="5.000",
        min_order="1.000",
    )

    client.force_login(admin)
    r = client.patch(f"/api/marketplace/products/{product.id}/", data={"title": "New2"})
    assert r.status_code in (status.HTTP_200_OK, status.HTTP_202_ACCEPTED)
