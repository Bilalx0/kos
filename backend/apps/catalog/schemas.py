from ninja import Schema
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class PricePairSchema(Schema):
    """Frontend expects {PKR: number, GBP: number} — never derived from FX."""
    PKR: Decimal
    GBP: Decimal


class FabricVariantSchema(Schema):
    id: UUID
    code: str
    name: str
    composition: str
    swatchImage: str
    inStock: bool

    @staticmethod
    def resolve_swatchImage(obj):
        return obj.swatch_image or ""

    @staticmethod
    def resolve_inStock(obj):
        return obj.in_stock


class ProductListSchema(Schema):
    """Lightweight schema for collection page."""
    id: UUID
    slug: str
    sku: str
    name: str
    category: str
    images: List[str]
    basePrice: PricePairSchema
    compareAtPrice: Optional[PricePairSchema] = None
    offersCustomStitching: bool

    @staticmethod
    def resolve_basePrice(obj):
        return {"PKR": obj.price_pkr, "GBP": obj.price_gbp}

    @staticmethod
    def resolve_compareAtPrice(obj):
        if obj.compare_at_price_pkr is None:
            return None
        return {"PKR": obj.compare_at_price_pkr, "GBP": obj.compare_at_price_gbp}

    @staticmethod
    def resolve_offersCustomStitching(obj):
        return obj.offers_custom_stitching


class ProductDetailSchema(Schema):
    """Full schema for PDP."""
    id: UUID
    slug: str
    sku: str
    name: str
    category: str
    description: str
    images: List[str]
    basePrice: PricePairSchema
    compareAtPrice: Optional[PricePairSchema] = None
    fabricVariants: List[FabricVariantSchema]
    availableSizes: List[str]
    offersCustomStitching: bool
    customStitchingSurcharge: PricePairSchema
    leadTimeDays: dict  # {standard: int, custom: int}

    @staticmethod
    def resolve_basePrice(obj):
        return {"PKR": obj.price_pkr, "GBP": obj.price_gbp}

    @staticmethod
    def resolve_compareAtPrice(obj):
        if obj.compare_at_price_pkr is None:
            return None
        return {"PKR": obj.compare_at_price_pkr, "GBP": obj.compare_at_price_gbp}

    @staticmethod
    def resolve_customStitchingSurcharge(obj):
        return {"PKR": obj.custom_stitching_surcharge_pkr, "GBP": obj.custom_stitching_surcharge_gbp}

    @staticmethod
    def resolve_availableSizes(obj):
        return obj.available_sizes or []

    @staticmethod
    def resolve_leadTimeDays(obj):
        return {"standard": obj.lead_time_days_standard, "custom": obj.lead_time_days_custom}