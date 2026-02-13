# marketplace/services.py
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Product, InventoryRecord
from decimal import Decimal

def adjust_product_stock(product_id, change_qty, change_type="ADJUST", performed_by=None, note=""):
    """
    Atomically adjust a product's stock and create an InventoryRecord.
    change_qty should be positive for IN, positive for OUT (change_type decides semantics).
    This function will raise if insufficient stock for an OUT operation.
    """
    product = get_object_or_404(Product, pk=product_id)

    with transaction.atomic():
        # Lock row
        p = Product.objects.select_for_update().get(pk=product.pk)
        # Interpret change_type: OUT decreases stock, IN increases
        if change_type == "OUT":
            if p.quantity < Decimal(change_qty):
                raise ValueError("Insufficient stock")
            p.quantity = p.quantity - Decimal(change_qty)
        else:
            # IN / ADJUST / RETURN
            p.quantity = p.quantity + Decimal(change_qty)
        p.save(update_fields=['quantity', 'updated_at'])

        InventoryRecord.objects.create(
            product=p,
            change_type=change_type,
            quantity=change_qty,
            note=note,
            performed_by=performed_by
        )
    return p
