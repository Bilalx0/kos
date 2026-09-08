from django.contrib import admin
from django.urls import path
from .api import api_v1

urlpatterns = [
    # Temporary Django Admin (for data seeding/debugging)
    path('django-admin/', admin.site.urls),
    
    # Headless API for Next.js (Storefront + Future Custom Admin)
    path('api/v1/', api_v1.urls),
]