from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from .models import Product
from .schemas import ProductListSchema, ProductDetailSchema

router = Router(tags=["Catalog"])


@router.get("/", response=List[ProductListSchema])
def list_products(request):
    """
    Collection page endpoint.
    Returns lightweight product list with fabric variants prefetched.
    """
    return Product.objects.filter(is_active=True).prefetch_related('fabric_variants')


@router.get("/{slug}", response=ProductDetailSchema)
def get_product(request, slug: str):
    """
    PDP endpoint.
    Returns full product detail with all fabric variants.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return product