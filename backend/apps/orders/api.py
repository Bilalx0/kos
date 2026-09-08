from ninja import Router
from django.db import transaction, IntegrityError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from typing import List
from .models import Order, OrderItem
from .schemas import (
    OrderCreateSchema,
    OrderResponseSchema,
    MeasurementSetSchema,
)
from common.validators import validate_measurements

router = Router(tags=["Orders"])


def _validate_order_items(items: List[dict]) -> List[str]:
    """
    Server-side validation of order items.
    Mirrors the frontend validation — never trust the client.
    """
    errors = []
    
    for idx, item in enumerate(items):
        mode = item.get('mode')
        
        # STANDARD mode requires size
        if mode == 'STANDARD' and not item.get('size'):
            errors.append(f"Item {idx}: Size is required for STANDARD mode")
        
        # CUSTOM mode requires measurements
        if mode == 'CUSTOM':
            measurements = item.get('measurements')
            if not measurements:
                errors.append(f"Item {idx}: Measurements are required for CUSTOM mode")
            else:
                # Validate measurement ranges
                meas_dict = measurements if isinstance(measurements, dict) else measurements.dict()
                unit = meas_dict.get('unit', 'inches')
                is_valid, field_errors = validate_measurements(meas_dict, unit)
                if not is_valid:
                    for err in field_errors:
                        errors.append(f"Item {idx} ({item.get('lineId')}): {err}")
    
    return errors


@router.post(
    "/validate",
    response={200: dict, 422: dict},
    url_name="validate_order",
)
def validate_order_payload(request: HttpRequest, payload: OrderCreateSchema):
    """
    Pre-checkout validation endpoint.
    Allows frontend to validate measurements BEFORE user enters payment info.
    Reduces failed Stripe charges and improves UX.
    """
    errors = _validate_order_items([item.dict() for item in payload.items])
    
    if errors:
        return 422, {"detail": "Validation failed", "errors": errors}
    
    return 200, {"detail": "Payload is valid"}


@router.post(
    "/",
    response={201: OrderResponseSchema, 200: OrderResponseSchema, 409: dict, 422: dict},
    url_name="create_order",
)
def create_order(request: HttpRequest, payload: OrderCreateSchema):
    """
    Idempotent order creation.
    
    - 201: Order created successfully
    - 200: Order already exists (idempotent retry) — return existing order
    - 409: Conflict (race condition fallback)
    - 422: Validation failed
    """
    # 1. Server-side validation (never trust the client)
    errors = _validate_order_items([item.dict() for item in payload.items])
    if errors:
        return 422, {"detail": "Validation failed", "errors": errors}
    
    # 2. Validate totals add up (prevent price tampering)
    calculated_subtotal = sum(
        float(item.unitPrice) * item.quantity for item in payload.items
    )
    if abs(float(payload.totals.subtotal) - calculated_subtotal) > 0.01:
        return 422, {"detail": "Subtotal mismatch. Please refresh your cart."}
    
    # 3. Atomic transaction for idempotency
    try:
        with transaction.atomic():
            # Check for existing order (idempotency)
            existing_order = Order.objects.filter(
                client_order_id=payload.clientOrderId
            ).first()
            
            if existing_order:
                # Idempotent hit — return existing order as 200 OK
                return 200, existing_order
            
            # Create order snapshot
            order = Order.objects.create(
                client_order_id=payload.clientOrderId,
                market=payload.market,
                currency=payload.currency,
                customer_first_name=payload.customer.firstName,
                customer_last_name=payload.customer.lastName,
                customer_email=payload.customer.email,
                customer_phone=payload.customer.phone,
                customer_whatsapp_opt_in=payload.customer.whatsappOptIn,
                shipping_line1=payload.customer.address.line1,
                shipping_line2=payload.customer.address.line2,
                shipping_city=payload.customer.address.city,
                shipping_postal_code=payload.customer.address.postalCode,
                shipping_country=payload.customer.address.country,
                subtotal=payload.totals.subtotal,
                shipping_cost=payload.totals.shipping,
                total=payload.totals.total,
                payment_method='STRIPE' if payload.market == 'INTL' else 'COD',
                payment_status='PENDING',
                status='RECEIVED',
            )
            
            # Create order items
            for item in payload.items:
                OrderItem.objects.create(
                    order=order,
                    line_id=item.lineId,
                    mode=item.mode,
                    sku=item.sku,
                    product_id=item.productId,
                    product_name=item.productName,
                    product_slug=item.productSlug,
                    fabric_variant_id=item.fabricVariantId,
                    fabric_variant_name=item.fabricVariantName,
                    size=item.size,
                    measurements=item.measurements.dict() if item.measurements else None,
                    currency=item.currency,
                    unit_price=item.unitPrice,
                    quantity=item.quantity,
                )
            
            # TODO: Phase 1 — Enqueue Celery task for order confirmation
            # send_order_confirmation.delay(order.id)
            
            return 201, order
            
    except IntegrityError:
        # Race condition fallback — two requests hit at the exact same millisecond
        # Return the existing order
        existing_order = Order.objects.filter(
            client_order_id=payload.clientOrderId
        ).first()
        if existing_order:
            return 200, existing_order
        return 409, {"detail": "Order creation conflict. Please try again."}


@router.get(
    "/{client_order_id}",
    response=OrderResponseSchema,
    url_name="get_order",
)
def get_order(request: HttpRequest, client_order_id: str):
    """
    Order lookup endpoint.
    Used by storefront confirmation page AND future admin dashboard.
    
    Uses prefetch_related to prevent N+1 queries.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        client_order_id=client_order_id
    )
    return order