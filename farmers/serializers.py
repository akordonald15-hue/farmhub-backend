# farmers/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Farmer, FarmerDocument, FarmerProduct, SupplyRecord


class FarmerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerDocument
        fields = ("id", "farmer", "name", "file_url", "uploaded_at", "verified", "notes")
        read_only_fields = ("id", "uploaded_at")


class FarmerProductSerializer(serializers.ModelSerializer):
    # Represent farmer as ID on write, nested read for convenience
    farmer = serializers.PrimaryKeyRelatedField(queryset=Farmer.objects.all(), required=False)
    farmer_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FarmerProduct
        fields = (
            "id", "farmer", "farmer_display", "title", "category", "description",
            "unit", "price_per_unit", "quantity_available", "min_order_quantity",
            "harvest_date", "is_active", "images", "metadata", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "farmer_display")

    def get_farmer_display(self, obj):
        if obj.farmer:
            return {"id": str(obj.farmer.id), "name": str(obj.farmer)}
        return None

    def validate_price_per_unit(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be non-negative.")
        return value

    def validate_quantity_available(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity must be non-negative.")
        return value


class SupplyRecordSerializer(serializers.ModelSerializer):
    farmer = serializers.PrimaryKeyRelatedField(queryset=Farmer.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=FarmerProduct.objects.all(), allow_null=True, required=False)
    status = serializers.ChoiceField(choices=SupplyRecord.STATUS_CHOICES, read_only=True)

    class Meta:
        model = SupplyRecord
        fields = (
            "id", "farmer", "product", "quantity", "unit", "supply_date",
            "status", "quality_notes", "received_by", "reference_code",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Supply quantity must be greater than zero.")
        return value

    def create(self, validated_data):
        # Ensure supply_date default if not provided
        if not validated_data.get("supply_date"):
            validated_data["supply_date"] = timezone.now()
        return super().create(validated_data)


class FarmerSerializer(serializers.ModelSerializer):
    products = FarmerProductSerializer(many=True, read_only=True)
    documents = FarmerDocumentSerializer(many=True, read_only=True)
    class Meta:
        model = Farmer
        fields = (
            "id", "user", "business_name", "contact_name", "phone", "email",
            "farm_type", "farm_size", "years_of_experience", "state", "lga",
            "address", "profile_image", "verified", "verification_note",
            "created_at", "updated_at", "metadata", "products", "documents",
        )
        read_only_fields = ("id", "created_at", "updated_at", "products", "documents")
