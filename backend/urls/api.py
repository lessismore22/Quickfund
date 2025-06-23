from django.urls import path, include

urlpatterns = [
    # Authentication & Users
    path('auth/', include('urls.auth')),
    path('users/', include('urls.users')),
    
    # Core Business Logic
    path('loans/', include('urls.loans')),
    path('payments/', include('urls.payments')),
    path('repayments/', include('urls.repayments')),
    
    # Communication & Notifications
    path('notifications/', include('urls.notifications')),
    
    # Admin & Analytics
    # path('analytics/', include('urls.analytics')),
    
    # System & Utilities
    path('system/', include('urls.system')),
]