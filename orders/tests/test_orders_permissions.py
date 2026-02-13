import pytest
from django.contrib.auth import get_user_model

from orders.permissions import IsOwnerOrAdmin
from orders.models import Order

User = get_user_model()


@pytest.mark.django_db
def test_is_owner_or_admin_permission():
    user = User.objects.create_user(username="u1", password="p")
    admin = User.objects.create_superuser(username="admin_perm", password="p", email="admin_perm@test.com")
    order = Order.objects.create(user=user, total_price=10)

    perm = IsOwnerOrAdmin()
    class Req: pass

    req = Req()
    req.user = user
    assert perm.has_object_permission(req, None, order) is True

    req.user = admin
    assert perm.has_object_permission(req, None, order) is True
