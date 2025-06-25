from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'', views.LoanViewSet, basename='loan')

urlpatterns = [
    # Loan application endpoints
   path('apply/', views.LoanApplicationViewSet.as_view({'post': 'create'}), name='loan_apply'),
    path('calculator/', views.LoanCalculatorView.as_view(), name='loan_calculator'),
    # path('eligibility-check/', views.EligibilityCheckView.as_view(), name='eligibility_check'),
    
    # # Loan management endpoints
    # path('<int:pk>/approve/', views.LoanApprovalView.as_view(), name='loan_approve'),
    # path('<int:pk>/reject/', views.LoanRejectionView.as_view(), name='loan_reject'),
    # path('<int:pk>/disburse/', views.LoanDisbursementView.as_view(), name='loan_disburse'),
    # path('<int:pk>/close/', views.LoanClosureView.as_view(), name='loan_close'),
    
    # # Loan status and history
    # path('my-loans/', views.UserLoansView.as_view(), name='user_loans'),
    # path('<int:pk>/status/', views.LoanStatusView.as_view(), name='loan_status'),
    # path('<int:pk>/history/', views.LoanHistoryView.as_view(), name='loan_history'),
    # path('<int:pk>/schedule/', views.RepaymentScheduleView.as_view(), name='repayment_schedule'),
    
    # # Credit scoring
    # path('credit-score/', views.CreditScoreView.as_view(), name='credit_score'),
    # path('credit-history/', views.CreditHistoryView.as_view(), name='credit_history'),
    
    # # Admin/Staff endpoints
    # path('pending-approval/', views.PendingLoansView.as_view(), name='pending_loans'),
    # path('overdue/', views.OverdueLoansView.as_view(), name='overdue_loans'),
    # path('statistics/', views.LoanStatisticsView.as_view(), name='loan_statistics'),
    
    # # Document management
    # path('<int:pk>/documents/', views.LoanDocumentsView.as_view(), name='loan_documents'),
    # path('<int:pk>/documents/upload/', views.LoanDocumentUploadView.as_view(), name='loan_document_upload'),
    
    # # Include router URLs for CRUD operations
    # path('', include(router.urls)),
]