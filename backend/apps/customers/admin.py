# apps/customers/admin.py
from django.contrib import admin
from .models import Customer, Address


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'whatsapp_opt_in', 'created_at']
    list_filter = ['whatsapp_opt_in']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    inlines = [AddressInline]
    readonly_fields = ['id', 'created_at', 'updated_at']