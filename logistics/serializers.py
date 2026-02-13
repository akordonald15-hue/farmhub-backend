# logistics/serializers.py
from rest_framework import serializers
from .models import LogisticsAgent, Vehicle, Dispatch, DispatchStatusUpdate


class LogisticsAgentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LogisticsAgent
        fields = ("id", "user", "full_name", "phone", "email", "active", "created_at")
        read_only_fields = ("id", "created_at")


class VehicleSerializer(serializers.ModelSerializer):
    driver = LogisticsAgentSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(queryset=LogisticsAgent.objects.all(), source="driver", write_only=True, required=False)

    class Meta:
        model = Vehicle
        fields = ("id", "vehicle_type", "registration_number", "driver", "driver_id", "capacity_description", "active", "created_at")
        read_only_fields = ("id", "created_at")


class DispatchStatusUpdateSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = DispatchStatusUpdate
        fields = ("id", "dispatch", "status", "note", "location", "created_by", "created_at")
        read_only_fields = ("id", "created_by", "created_at")


class DispatchSerializer(serializers.ModelSerializer):
    assigned_agent = LogisticsAgentSerializer(read_only=True)
    assigned_agent_id = serializers.PrimaryKeyRelatedField(queryset=LogisticsAgent.objects.all(), source="assigned_agent", write_only=True, required=False)
    assigned_vehicle = VehicleSerializer(read_only=True)
    assigned_vehicle_id = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all(), source="assigned_vehicle", write_only=True, required=False)
    status_updates = DispatchStatusUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Dispatch
        fields = (
            "id", "order", "supply_record", "reference_code", "pickup_address", "dropoff_address",
            "assigned_agent", "assigned_agent_id", "assigned_vehicle", "assigned_vehicle_id",
            "status", "estimated_pickup_time", "estimated_delivery_time", "pickup_time", "delivery_time",
            "proof_of_delivery_url", "receiver_name", "notes", "created_by", "cost",
            "created_at", "updated_at", "status_updates",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at", "status_updates")

    def create(self, validated_data):
        # set created_by automatically from context user (if provided)
        user = self.context.get("request").user if self.context.get("request") else None
        validated_data.setdefault("created_by", user)
        return super().create(validated_data)
