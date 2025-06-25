from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="QuickCash API",
        default_version='v1',
        description="Quick Cash Loan Management System API",
        terms_of_service="https://www.quickfund_api.com/terms/",
        contact=openapi.Contact(email="contact@quickcash.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api-docs/', include_docs_urls(title='QuickCash API')),
    
    # API v1 endpoints
    path('api/v1/auth/', include('quickfund_api.users.urls')),
    path('api/v1/loans/', include('quickfund_api.loans.urls')),
    path('api/v1/payments/', include('quickfund_api.payments.urls')),
    path('api/v1/notifications/', include('quickfund_api.notifications.urls')),
    
    # Health check endpoint
    # path('health/', include('monitoring.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)