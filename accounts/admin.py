# Accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification, CustomerProfile, FarmerProfile, VendorProfile, LogisticsAgentProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "role", "is_staff", "is_verified", "is_active")
    list_filter = ("role", "is_staff", "is_verified")
    search_fields = ("email", "full_name")
    ordering = ("email",)
    readonly_fields = ("date_joined", "updated_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "username")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_superuser", "is_active", "is_verified")}),
        ("Important dates", {"fields": ("date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )

admin.site.register(EmailVerification)
admin.site.register(CustomerProfile)
admin.site.register(FarmerProfile)
admin.site.register(VendorProfile)
admin.site.register(LogisticsAgentProfile)
