# logistics/admin.py
from django.contrib import admin
from .models import LogisticsAgent, Vehicle, Dispatch, DispatchStatusUpdate


@admin.register(LogisticsAgent)
class LogisticsAgentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "active", "created_at")
    search_fields = ("full_name", "phone", "email")
    list_filter = ("active",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "vehicle_type", "driver", "active", "created_at")
    search_fields = ("registration_number", "driver__full_name")
    list_filter = ("vehicle_type", "active")


@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "order", "supply_record", "assigned_agent", "status", "pickup_time", "delivery_time", "created_at")
    search_fields = ("reference_code", "assigned_agent__full_name", "order__id", "supply_record__id")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DispatchStatusUpdate)
class DispatchStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("dispatch", "status", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("dispatch__reference_code",)
