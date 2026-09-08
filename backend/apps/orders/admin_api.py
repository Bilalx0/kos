from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from typing import List, Optional, Literal
from .models import Order, OrderItem
from .schemas import OrderResponseSchema

router = Router(tags=["Admin"])


# --- State Machine Definition ---
# Explicit transition map — prevents illegal state jumps
# The admin dashboard MUST call /transition, never PATCH /status directly
ALLOWED_TRANSITIONS = {
    'RECEIVED': ['MEASUREMENT_REVIEW', 'CANCELLED'],
    'MEASUREMENT_REVIEW': ['CONFIRMED_WITH_CLIENT', 'CANCELLED'],
    'CONFIRMED_WITH_CLIENT': ['CUTTING', 'CANCELLED'],
    'CUTTING': ['STITCHING', 'CANCELLED'],
    'STITCHING': ['EMBELLISHMENT', 'QC', 'CANCELLED'],
    'EMBELLISHMENT': ['QC', 'CANCELLED'],
    'QC': ['SHIPPED', 'CANCELLED'],
    'SHIPPED': ['DELIVERED'],  # Can't cancel after shipping
    'DELIVERED': [],  # Terminal state
    'CANCELLED': [],  # Terminal state
}


class OrderTransitionSchema(Schema):
    """Request schema for state transitions."""
    newStatus: str
    adminNotes: Optional[str] = None


class OrderListSchema(Schema):
    """Lightweight schema for admin order list."""
    id: str
    clientOrderId: str
    customerName: str
    customerEmail: str
    market: str
    status: str
    paymentStatus: str
    total: float
    itemCount: int
    hasBespokeItems: bool
    createdAt: str

    @staticmethod
    def resolve_clientOrderId(obj):
        return str(obj.client_order_id)

    @staticmethod
    def resolve_customerName(obj):
        return f"{obj.customer_first_name} {obj.customer_last_name}"

    @staticmethod
    def resolve_customerEmail(obj):
        return obj.customer_email

    @staticmethod
    def resolve_itemCount(obj):
        return obj.items.count()

    @staticmethod
    def resolve_hasBespokeItems(obj):
        return obj.items.filter(mode='CUSTOM').exists()

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()


@router.get(
    "/orders",
    response=List[OrderListSchema],
    url_name="admin_list_orders",
)
def admin_list_orders(
    request,
    status: Optional[str] = None,
    market: Optional[str] = None,
    payment_status: Optional[str] = None,
    search: Optional[str] = None,
    has_bespoke: Optional[bool] = None,
):
    """
    Admin order list with filtering.
    
    Designed for the custom admin dashboard:
    - Filter by status, market, payment status
    - Search by customer name/email/phone/order ID
    - Filter for bespoke-only orders
    - Returns lightweight list (no items prefetched — use detail endpoint for that)
    """
    queryset = Order.objects.all()
    
    # Apply filters
    if status:
        queryset = queryset.filter(status=status)
    if market:
        queryset = queryset.filter(market=market)
    if payment_status:
        queryset = queryset.filter(payment_status=payment_status)
    if search:
        queryset = queryset.filter(
            Q(customer_first_name__icontains=search) |
            Q(customer_last_name__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(client_order_id__icontains=search)
        )
    if has_bespoke is not None:
        if has_bespoke:
            queryset = queryset.filter(items__mode='CUSTOM').distinct()
        else:
            queryset = queryset.exclude(items__mode='CUSTOM')
    
    return queryset.order_by('-created_at')[:100]  # Limit to 100 for Phase 1


@router.get(
    "/orders/{client_order_id}",
    response=OrderResponseSchema,
    url_name="admin_get_order",
)
def admin_get_order(request, client_order_id: str):
    """
    Rich admin order detail.
    
    Returns all data needed for the admin dashboard:
    - Full customer info
    - All items with measurements (for bespoke)
    - State transition options
    """
    order = get_object_or_404(
        Order.objects.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.all().order_by('created_at'))
        ),
        client_order_id=client_order_id
    )
    return order


@router.get(
    "/orders/{client_order_id}/transitions",
    response=dict,
    url_name="admin_get_transitions",
)
def admin_get_allowed_transitions(request, client_order_id: str):
    """
    Returns allowed next states for an order.
    The admin dashboard uses this to render transition buttons.
    """
    order = get_object_or_404(Order, client_order_id=client_order_id)
    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    
    return {
        "currentStatus": order.status,
        "allowedTransitions": allowed,
        "isTerminal": order.status in ['DELIVERED', 'CANCELLED'],
    }


@router.post(
    "/orders/{client_order_id}/transition",
    response={200: OrderResponseSchema, 400: dict, 404: dict},
    url_name="admin_transition_order",
)
def admin_transition_order(
    request,
    client_order_id: str,
    payload: OrderTransitionSchema,
):
    """
    Explicit state transition endpoint.
    
    The admin dashboard calls this to move an order through the state machine.
    Prevents illegal transitions (e.g., jumping from RECEIVED to SHIPPED).
    
    Future enhancement: Log transitions in OrderHistory model for audit trail.
    """
    order = get_object_or_404(Order, client_order_id=client_order_id)
    
    new_status = payload.newStatus
    allowed = ALLOWED_TRANSITIONS.get(order.status, [])
    
    if new_status not in allowed:
        return 400, {
            "detail": f"Invalid transition from {order.status} to {new_status}",
            "currentStatus": order.status,
            "allowedTransitions": allowed,
        }
    
    # Perform transition
    order.status = new_status
    if payload.adminNotes:
        order.notes = f"{order.notes}\n[{new_status}] {payload.adminNotes}".strip()
    order.save(update_fields=['status', 'notes', 'updated_at'])
    
    # TODO: Phase 2 — Log transition in OrderHistory model
    # TODO: Phase 3 — Trigger notifications based on transition (e.g., WhatsApp on SHIPPED)
    
    return 200, order