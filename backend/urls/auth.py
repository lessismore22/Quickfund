from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from quickfund_api.users.views import (
    UserRegistrationView,
    CustomTokenObtainPairView,
    # PasswordResetView,
    # PasswordChangeView,
    # LogoutView,
)

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    # path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth_token_refresh'),
    
    # Password Management
    # path('password/reset/', PasswordResetView.as_view(), name='auth_password_reset'),
    # path('password/change/', PasswordChangeView.as_view(), name='auth_password_change'),
    # path('password/reset/confirm/', PasswordResetView.as_view(), name='auth_password_reset_confirm'),
]