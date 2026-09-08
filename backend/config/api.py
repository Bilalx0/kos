from ninja import NinjaAPI

# Initialize the versioned API
api_v1 = NinjaAPI(
    title="KOS API v1",
    version="1.0.0",
    urls_namespace="api-v1",
    docs_url="/docs/",
)

# Import routers
from catalog.api import router as catalog_router
from orders.api import router as orders_router
from orders.admin_api import router as admin_router

# Register routers
api_v1.add_router("/catalog/", catalog_router)
api_v1.add_router("/orders/", orders_router)
api_v1.add_router("/admin/", admin_router)  # Future custom admin dashboard