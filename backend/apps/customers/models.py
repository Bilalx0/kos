from django.db import models
import uuid


class Customer(models.Model):
    """
    Guest customer record.
    Phone stored in E.164 format for future WhatsApp integration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(
        max_length=20,
        help_text="E.164 format: +447123456789 or +923001234567"
    )
    whatsapp_opt_in = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'phone']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Address(models.Model):
    """
    Shipping/billing address.
    Postal code is optional (many PK addresses lack postcodes).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=2,
        help_text="ISO-3166 alpha-2 country code"
    )
    address_type = models.CharField(
        max_length=10,
        choices=[('shipping', 'Shipping'), ('billing', 'Billing')],
        default='shipping'
    )
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.line1}, {self.city}, {self.country}"