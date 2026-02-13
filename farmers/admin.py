# farmers/admin.py
from django.contrib import admin
from .models import Farmer, FarmerDocument, FarmerProduct, SupplyRecord


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ("contact_name", "business_name", "phone", "state", "lga", "farm_type", "verified", "created_at")
    list_filter = ("verified", "farm_type", "state", "created_at")
    search_fields = ("contact_name", "business_name", "phone", "email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(FarmerDocument)
class FarmerDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "farmer", "uploaded_at", "verified")
    list_filter = ("verified", "uploaded_at")
    search_fields = ("name", "farmer__contact_name", "farmer__business_name")


class FarmerProductInline(admin.TabularInline):
    model = FarmerProduct
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("title", "category", "unit", "price_per_unit", "quantity_available", "is_active", "created_at")


@admin.register(FarmerProduct)
class FarmerProductAdmin(admin.ModelAdmin):
    list_display = ("title", "farmer", "category", "unit", "price_per_unit", "quantity_available", "is_active", "created_at")
    list_filter = ("category", "unit", "is_active", "created_at")
    search_fields = ("title", "farmer__contact_name", "farmer__business_name")
    inlines = []
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(SupplyRecord)
class SupplyRecordAdmin(admin.ModelAdmin):
    list_display = ("farmer", "product", "quantity", "unit", "status", "supply_date", "created_at")
    list_filter = ("status", "supply_date", "created_at")
    search_fields = ("farmer__contact_name", "farmer__business_name", "product__title")
    readonly_fields = ("created_at", "updated_at")
    actions = ["mark_approved", "mark_rejected"]

    def mark_approved(self, request, queryset):
        updated = queryset.update(status="APPROVED")
        self.message_user(request, f"{updated} supply record(s) marked as APPROVED.")
    mark_approved.short_description = "Mark selected supply records as APPROVED"

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status="REJECTED")
        self.message_user(request, f"{updated} supply record(s) marked as REJECTED.")
    mark_rejected.short_description = "Mark selected supply records as REJECTED"
