# marketplace/serializers.py
from rest_framework import serializers
from .models import Category, Product, ProductImage, InventoryRecord
from farmers.serializers import FarmerSerializer  # nested display (safe if farmers is installed)


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "created_at", "products_count")
        read_only_fields = ("id", "created_at", "products_count")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "product", "image_url", "alt_text", "order", "created_at")
        read_only_fields = ("id", "created_at")


class ProductListSerializer(serializers.ModelSerializer):
    farmer = serializers.PrimaryKeyRelatedField(read_only=True)
    farmer_display = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "title", "slug", "farmer", "farmer_display", "category", "category_display",
            "description", "unit", "price", "quantity", "min_order", "is_active", "featured",
            "images", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at", "farmer_display", "images", "category_display")

    def get_farmer_display(self, obj):
        return {"id": str(obj.farmer.id), "name": str(obj.farmer)}

    def get_category_display(self, obj):
        if obj.category:
            return {"id": str(obj.category.id), "name": obj.category.name}
        return None


class ProductDetailSerializer(ProductListSerializer):
    metadata = serializers.JSONField(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ("metadata",)


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Use this for create & update operations; farmer is inferred for non-staff users.
    """
    class Meta:
        model = Product
        fields = (
            "id", "farmer", "title", "slug", "category", "description",
            "unit", "price", "quantity", "min_order", "is_active", "featured", "metadata"
        )
        read_only_fields = ("id", "slug")

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be a non-negative number.")
        return value

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be non-negative.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        # If non-staff and has linked farmer_profile, set farmer automatically
        if user and user.is_authenticated and not user.is_staff:
            if hasattr(user, "farmer_profile"):
                validated_data["farmer"] = user.farmer_profile
        return super().create(validated_data)


class InventoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryRecord
        fields = ("id", "product", "change_type", "quantity", "note", "performed_by", "created_at")
        read_only_fields = ("id", "performed_by", "created_at")
