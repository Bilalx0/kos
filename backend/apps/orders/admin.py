# apps/orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['line_id', 'mode', 'sku', 'product_name', 'fabric_variant_name', 'size', 'measurements', 'unit_price', 'quantity']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['client_order_id', 'customer_first_name', 'customer_last_name', 'market', 'status', 'payment_status', 'total', 'created_at']
    list_filter = ['status', 'payment_status', 'market', 'payment_method']
    search_fields = ['client_order_id', 'customer_first_name', 'customer_last_name', 'customer_email', 'customer_phone']
    readonly_fields = ['id', 'client_order_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('client_order_id', 'market', 'currency', 'status', 'payment_method', 'payment_status')
        }),
        ('Customer', {
            'fields': ('customer_first_name', 'customer_last_name', 'customer_email', 'customer_phone', 'customer_whatsapp_opt_in')
        }),
        ('Shipping Address', {
            'fields': ('shipping_line1', 'shipping_line2', 'shipping_city', 'shipping_postal_code', 'shipping_country')
        }),
        ('Financials', {
            'fields': ('subtotal', 'shipping_cost', 'total')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )