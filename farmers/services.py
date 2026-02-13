# farmers/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import FarmerProduct


def reserve_product_stock(product_id: int, quantity: int) -> None:
    """
    Atomically reserve stock for a single FarmerProduct.
    
    Raises ValidationError if stock is insufficient.
    """
    if quantity <= 0:
        raise ValidationError("Quantity to reserve must be positive.")

    with transaction.atomic():
        # Lock the product row for update to prevent race conditions
        product = FarmerProduct.objects.select_for_update().get(id=product_id)
        if product.quantity_available < quantity:
            raise ValidationError(
                f"Insufficient stock for {product.title}. Available: {product.quantity_available}"
            )
        product.quantity_available -= quantity
        product.save(update_fields=['quantity_available'])


def release_product_stock(product_id: int, quantity: int) -> None:
    """
    Atomically release previously reserved stock for a FarmerProduct.
    Useful for order cancellations or rollbacks.
    """
    if quantity <= 0:
        raise ValidationError("Quantity to release must be positive.")

    with transaction.atomic():
        product = FarmerProduct.objects.select_for_update().get(id=product_id)
        product.quantity_available += quantity
        product.save(update_fields=['quantity_available'])


def reserve_bulk_stock(items: list[dict]) -> None:
    """
    Reserve multiple products atomically.
    `items` is a list of dicts: [{"product_id": 1, "quantity": 3}, ...]
    
    Raises ValidationError if any product has insufficient stock.
    All reservations succeed or none do (atomic).
    """
    if not items:
        raise ValidationError("No items provided for reservation.")

    with transaction.atomic():
        # Lock all products at once
        product_ids = [item['product_id'] for item in items]
        products = FarmerProduct.objects.select_for_update().filter(id__in=product_ids)
        product_map = {p.id: p for p in products}

        # Check availability first
        for item in items:
            pid = item['product_id']
            qty = item['quantity']
            if qty <= 0:
                raise ValidationError("Quantities must be positive.")
            if pid not in product_map:
                raise ValidationError(f"Product with id {pid} not found.")
            if product_map[pid].quantity_available < qty:
                raise ValidationError(
                    f"Insufficient stock for {product_map[pid].title}. Available: {product_map[pid].quantity_available}"
                )

        # Deduct stock
        for item in items:
            product_map[item['product_id']].quantity_available -= item['quantity']
            product_map[item['product_id']].save(update_fields=['quantity_available'])
