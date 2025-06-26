from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'repayments', views.RepaymentViewSet, basename='repayment')

urlpatterns = [
    # Payment processing
    path('initiate/', views.PaymentInitiationView.as_view(), name='payment_initiate'),
    path('verify/', views.PaymentVerificationView.as_view(), name='payment_verify'),
    path('callback/paystack/', views.PaystackCallbackView.as_view(), name='paystack_callback'),
    
    # Loan repayments
    path('loans/<int:loan_id>/repay/', views.LoanRepaymentView.as_view(), name='loan_repayment'),
    path('loans/<int:loan_id>/payment-methods/', views.PaymentMethodsView.as_view(), name='payment_methods'),
    path('loans/<int:loan_id>/UserPaymentHistory/', views.UserPaymentHistoryView.as_view(), name='payment_history'),
    
    # Payment management
    path('history/', views.UserPaymentHistoryView.as_view(), name='user_payment_history'),
    path('<int:pk>/receipt/', views.PaymentReceiptView.as_view(), name='payment_receipt'),
    path('<int:pk>/refund/', views.PaymentRefundView.as_view(), name='payment_refund'),
    
    # Payment schedules and reminders
    path('schedule/', views.PaymentScheduleView.as_view(), name='payment_schedule'),
    path('upcoming/', views.UpcomingPaymentsView.as_view(), name='upcoming_payments'),
    path('overdue/', views.OverduePaymentsView.as_view(), name='overdue_payments'),
    
    # Webhook endpoints
    path('webhooks/paystack/', views.PaystackWebhookView.as_view(), name='paystack_webhook'),
    
    # Admin/Staff endpoints
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('reconciliation/', views.PaymentReconciliationView.as_view(), name='payment_reconciliation'),
    path('statistics/', views.PaymentStatisticsView.as_view(), name='payment_statistics'),
    
    # Payment analytics
    # path('analytics/revenue/', views.RevenueAnalyticsView.as_view(), name='revenue_analytics'),
    # path('analytics/defaults/', views.DefaultAnalyticsView.as_view(), name='default_analytics'),
    
    # Include router URLs
    path('', include(router.urls)),
]