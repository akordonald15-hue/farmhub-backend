# marketplace/admin.py
from django.contrib import admin
from .models import Category, Product, ProductImage, InventoryRecord

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'farmer', 'price', 'quantity', 'is_active', 'featured', 'created_at')
    list_filter = ('is_active', 'featured', 'category')
    search_fields = ('title', 'farmer__contact_name', 'farmer__business_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_url', 'order', 'created_at')
    search_fields = ('product__title',)


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity', 'performed_by', 'created_at')
    list_filter = ('change_type',)
    search_fields = ('product__title',)
