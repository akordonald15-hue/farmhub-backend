from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from .models import Order, OrderItem
from products.models import MenuItem
from products.serializers import MenuItemSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_detail = MenuItemSerializer(source='menu_item', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_detail', 'quantity', 'price']
        read_only_fields = ['id', 'menu_item_detail', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer = serializers.ReadOnlyField(source='user.username')
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'total_price', 'address', 'phone',
            'created_at', 'items', 'paid', 'paystack_reference'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'paid', 'paystack_reference']

    # FIELD VALIDATION
    def validate_address(self, value):
        if value is None:
            return value
        value = value.strip()
        if len(value) < 5:  # Stronger validation
            raise serializers.ValidationError("Address is too short (minimum 5 characters).")
        return value

    def validate_phone(self, value):
        if value is None:
            return value
        value = value.strip()
        if not value.isdigit() or len(value) < 8:
            raise serializers.ValidationError("Invalid phone number.")
        return value

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        return value

    # CREATE ORDER
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Safe context retrieval
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None

        order = Order.objects.create(user=user, **validated_data)
        total = Decimal('0.00')

        for item in items_data:
            # Flexible menu item lookup
            menu_item_obj = None
            if isinstance(item.get('menu_item'), int):
                menu_item_obj = MenuItem.objects.get(id=item.get('menu_item'))
            elif isinstance(item.get('menu_id'), int):
                menu_item_obj = MenuItem.objects.get(id=item.get('menu_id'))
            elif isinstance(item.get('menu_item'), MenuItem):
                menu_item_obj = item.get('menu_item')
            else:
                raise serializers.ValidationError("Invalid menu_item entry.")

            if not menu_item_obj.is_available:
                raise serializers.ValidationError(f"Item '{menu_item_obj.name}' is not available.")

            quantity = int(item.get('quantity', 1))
            if quantity <= 0:
                raise serializers.ValidationError(f"Invalid quantity for '{menu_item_obj.name}'.")

            price = Decimal(menu_item_obj.price)

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item_obj,
                quantity=quantity,
                price=price
            )

            total += price * quantity

        order.total_price = total
        order.save()
        return order

    # UPDATE ORDER
    def update(self, instance, validated_data):
        validated_data.pop('items', None)
        return super().update(instance, validated_data)