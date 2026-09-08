# apps/catalog/admin.py
from django.contrib import admin
from .models import Product, FabricVariant


class FabricVariantInline(admin.TabularInline):
    model = FabricVariant
    extra = 1
    fields = ['code', 'name', 'composition', 'swatch_image', 'in_stock']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price_pkr', 'price_gbp', 'offers_custom_stitching', 'is_active']
    list_filter = ['category', 'offers_custom_stitching', 'is_active']
    search_fields = ['name', 'sku', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FabricVariantInline]
    readonly_fields = ['id', 'created_at', 'updated_at']