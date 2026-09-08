from ninja import Schema
from typing import List, Optional, Literal
from uuid import UUID
from decimal import Decimal
from datetime import datetime


# --- Measurement Schema ---
class MeasurementSetSchema(Schema):
    unit: Literal['inches', 'cm']
    shirtLength: float
    bust: float
    shoulder: float
    waist: float
    hips: float
    sleeveLength: float
    armhole: float
    specialNotes: Optional[str] = None


# --- Order Item Schemas ---
class OrderItemCreateSchema(Schema):
    """Input schema for creating an order item."""
    lineId: str
    productId: str
    productSlug: str
    productName: str
    sku: str
    fabricVariantId: str
    fabricVariantName: str
    currency: Literal['PKR', 'GBP']
    unitPrice: Decimal
    quantity: int
    mode: Literal['STANDARD', 'CUSTOM']
    size: Optional[str] = None
    measurements: Optional[MeasurementSetSchema] = None


class OrderItemResponseSchema(Schema):
    """Response schema — rich data for both storefront confirmation and admin dashboard."""
    id: UUID
    lineId: str
    mode: str
    sku: str
    productName: str
    productSlug: str
    fabricVariantName: str
    size: Optional[str] = None
    measurements: Optional[dict] = None
    unitPrice: Decimal
    quantity: int

    @staticmethod
    def resolve_lineId(obj):
        return obj.line_id

    @staticmethod
    def resolve_productName(obj):
        return obj.product_name

    @staticmethod
    def resolve_productSlug(obj):
        return obj.product_slug

    @staticmethod
    def resolve_fabricVariantName(obj):
        return obj.fabric_variant_name


# --- Customer & Address Schemas ---
class CustomerAddressSchema(Schema):
    line1: str
    line2: Optional[str] = None
    city: str
    postalCode: Optional[str] = None
    country: str  # ISO-3166 alpha-2


class CustomerSchema(Schema):
    firstName: str
    lastName: str
    email: str
    phone: str  # E.164 format
    whatsappOptIn: bool
    address: CustomerAddressSchema


class TotalsSchema(Schema):
    subtotal: Decimal
    shipping: Decimal
    total: Decimal


class AttributionSchema(Schema):
    source: Optional[str] = None
    campaign: Optional[str] = None


# --- Order Creation Schema ---
class OrderCreateSchema(Schema):
    clientOrderId: UUID
    market: Literal['PK', 'INTL']
    currency: Literal['PKR', 'GBP']
    customer: CustomerSchema
    items: List[OrderItemCreateSchema]
    totals: TotalsSchema
    attribution: Optional[AttributionSchema] = None


# --- Order Response Schema ---
class OrderResponseSchema(Schema):
    """
    Rich response for storefront confirmation AND future admin dashboard.
    Includes all data needed to render a clean admin order detail view.
    """
    id: UUID
    clientOrderId: UUID
    market: str
    currency: str
    status: str
    paymentMethod: str
    paymentStatus: str
    
    # Customer info
    customerName: str
    customerEmail: str
    customerPhone: str
    whatsappOptIn: bool
    
    # Shipping
    shippingCity: str
    shippingCountry: str
    
    # Financials
    subtotal: Decimal
    shippingCost: Decimal
    total: Decimal
    
    # Items
    items: List[OrderItemResponseSchema]
    
    # Metadata
    createdAt: datetime
    updatedAt: datetime

    @staticmethod
    def resolve_clientOrderId(obj):
        return obj.client_order_id

    @staticmethod
    def resolve_paymentMethod(obj):
        return obj.payment_method

    @staticmethod
    def resolve_paymentStatus(obj):
        return obj.payment_status

    @staticmethod
    def resolve_customerName(obj):
        return f"{obj.customer_first_name} {obj.customer_last_name}"

    @staticmethod
    def resolve_customerEmail(obj):
        return obj.customer_email

    @staticmethod
    def resolve_customerPhone(obj):
        return obj.customer_phone

    @staticmethod
    def resolve_whatsappOptIn(obj):
        return obj.customer_whatsapp_opt_in

    @staticmethod
    def resolve_shippingCity(obj):
        return obj.shipping_city

    @staticmethod
    def resolve_shippingCountry(obj):
        return obj.shipping_country

    @staticmethod
    def resolve_shippingCost(obj):
        return obj.shipping_cost

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at