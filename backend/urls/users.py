from django.urls import path
from quickfund_api.users.views import (
    UserProfileView,
    # UserListView,
    # UserDetailView,
    # VerifyPhoneView,
    # VerifyBVNView,
    # UpdateProfileView,
)

urlpatterns = [
    # User Profile Management
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    # path('profile/update/', UpdateProfileView.as_view(), name='user_profile_update'),
    
    # # User Verification
    # path('verify/phone/', VerifyPhoneView.as_view(), name='user_verify_phone'),
    # path('verify/phone/confirm/', VerifyPhoneView.as_view(), name='user_verify_phone_confirm'),
    # path('verify/bvn/', VerifyBVNView.as_view(), name='user_verify_bvn'),
    
    # # User Management (Admin)
    # path('', UserListView.as_view(), name='user_list'),
    # path('<uuid:user_id>/', UserDetailView.as_view(), name='user_detail'),
    # path('<uuid:user_id>/activate/', UserDetailView.as_view(), name='user_activate'),
    # path('<uuid:user_id>/deactivate/', UserDetailView.as_view(), name='user_deactivate'),
]