from django.urls import path
from quickfund_api.payments.views import (
    # InitiatePaymentView,
    # VerifyPaymentView,
    # PaymentHistoryView,
    # PaymentMethodsView,
    PaymentCallbackView,
)

urlpatterns = [
    # Payment Processing
    # path('initiate/', InitiatePaymentView.as_view(), name='payment_initiate'),
    # path('verify/<str:reference>/', VerifyPaymentView.as_view(), name='payment_verify'),
    # path('history/', PaymentHistoryView.as_view(), name='payment_history'),
    
    # # Payment Methods
    # path('methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    # path('methods/add/', PaymentMethodsView.as_view(), name='payment_method_add'),
    # path('methods/<uuid:method_id>/remove/', PaymentMethodsView.as_view(), name='payment_method_remove'),
    
    # Payment Gateway Callbacks
    path('callbacks/paystack/', PaymentCallbackView, name='payment_callback_paystack'),
    path('callbacks/flutterwave/', PaymentCallbackView, name='payment_callback_flutterwave'),
    path('callbacks/interswitch/', PaymentCallbackView, name='payment_callback_interswitch'),
    
    # Virtual Accounts
#     path('virtual-accounts/', PaymentMethodsView.as_view(), name='virtual_accounts'),
#     path('virtual-accounts/create/', PaymentMethodsView.as_view(), name='virtual_account_create'),
]