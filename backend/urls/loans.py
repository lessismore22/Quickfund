from django.urls import path
from quickfund_api.loans.views import (
    LoanListView,
    # LoanDetailView,
    # LoanApplicationView,
    # LoanApprovalView,
    # LoanDisbursementView,
    # LoanCalculatorView,
)

urlpatterns = [
    # # Loan Management
    # path('', LoanListView.as_view(), name='loan_list'),
    # path('apply/', LoanApplicationView.as_view(), name='loan_apply'),
    # path('calculator/', LoanCalculatorView.as_view(), name='loan_calculator'),
    # path('<uuid:loan_id>/', LoanDetailView.as_view(), name='loan_detail'),
    
    # # Loan Processing (Admin/Staff)
    # path('<uuid:loan_id>/approve/', LoanApprovalView.as_view(), name='loan_approve'),
    # path('<uuid:loan_id>/reject/', LoanApprovalView.as_view(), name='loan_reject'),
    # path('<uuid:loan_id>/disburse/', LoanDisbursementView.as_view(), name='loan_disburse'),
    # path('<uuid:loan_id>/cancel/', LoanDetailView.as_view(), name='loan_cancel'),
    
    # Loan Status & History
    path('history/', LoanListView.as_view(), name='loan_history'),
    path('active/', LoanListView.as_view(), name='loan_active'),
    path('completed/', LoanListView.as_view(), name='loan_completed'),
    path('overdue/', LoanListView.as_view(), name='loan_overdue'),
]