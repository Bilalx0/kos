from django.db import models
import uuid


class Product(models.Model):
    """
    Core product model.
    Stores explicit PKR and GBP prices — never derived from exchange rates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=[
            ('pret', 'Ready-to-Wear'),
            ('unstitched', 'Unstitched'),
            ('formal', 'Formal'),
            ('bridal', 'Bridal'),
        ],
        db_index=True,
    )
    description = models.TextField(blank=True)
    images = models.JSONField(default=list, help_text="Array of image URLs")
    
    # Dual pricing — explicit, never derived
    price_pkr = models.DecimalField(max_digits=10, decimal_places=0)
    price_gbp = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price_pkr = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    compare_at_price_gbp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Available sizes (stored as JSON array for flexibility)
    available_sizes = models.JSONField(
        default=list,
        help_text="Array of sizes, e.g. ['XS', 'S', 'M', 'L', 'XL']"
    )
    
    # Bespoke stitching options
    offers_custom_stitching = models.BooleanField(default=False, db_index=True)
    custom_stitching_surcharge_pkr = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    custom_stitching_surcharge_gbp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Lead times
    lead_time_days_standard = models.IntegerField(default=4)
    lead_time_days_custom = models.IntegerField(default=21)
    
    # Metadata
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['offers_custom_stitching', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class FabricVariant(models.Model):
    """
    Fabric/color variants for a product.
    Each variant has its own stock status and swatch image.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='fabric_variants'
    )
    code = models.CharField(
        max_length=20,
        help_text="Short code for SKU derivation, e.g. 'IVR' for Ivory"
    )
    name = models.CharField(max_length=255, help_text="e.g. 'Silk Cotton — Ivory'")
    composition = models.CharField(max_length=255, blank=True)
    swatch_image = models.URLField(blank=True)
    in_stock = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [['product', 'code']]

    def __str__(self):
        return f"{self.product.name} — {self.name}"