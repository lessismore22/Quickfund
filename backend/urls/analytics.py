# from django.urls import path
# from quickfund_api.analytics.views import (
#     AnalyticsOverviewView,
#     LoanAnalyticsView,
#     PaymentAnalyticsView,
#     UserAnalyticsView,
#     PerformanceMetricsView,
# )

# urlpatterns = [
#     # Overview Analytics
#     path('overview/', AnalyticsOverviewView.as_view(), name='analytics_overview'),
#     path('summary/', AnalyticsOverviewView.as_view(), name='analytics_summary'),
    
#     # Loan Analytics
#     path('loans/', LoanAnalyticsView.as_view(), name='analytics_loans'),
#     path('loans/approval-rate/', LoanAnalyticsView.as_view(), name='analytics_loan_approval'),
#     path('loans/default-rate/', LoanAnalyticsView.as_view(), name='analytics_loan_default'),
#     path('loans/disbursement/', LoanAnalyticsView.as_view(), name='analytics_loan_disbursement'),
    
#     # Payment Analytics
#     path('payments/', PaymentAnalyticsView.as_view(), name='analytics_payments'),
#     path('payments/collection-rate/', PaymentAnalyticsView.as_view(), name='analytics_payment_collection'),
#     path('payments/methods/', PaymentAnalyticsView.as_view(), name='analytics_payment_methods'),
    
#     # User Analytics
#     path('users/', UserAnalyticsView.as_view(), name='analytics_users'),
#     path('users/acquisition/', UserAnalyticsView.as_view(), name='analytics_user_acquisition'),
#     path('users/retention/', UserAnalyticsView.as_view(), name='analytics_user_retention'),
#     path('users/demographics/', UserAnalyticsView.as_view(), name='analytics_user_demographics'),
    
#     # Performance Metrics
#     path('performance/', PerformanceMetricsView.as_view(), name='analytics_performance'),
#     path('performance/portfolio/', PerformanceMetricsView.as_view(), name='analytics_portfolio'),
#     path('performance/risk/', PerformanceMetricsView.as_view(), name='analytics_risk'),
# ]
