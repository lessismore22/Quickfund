from django.urls import path
from quickfund_api.payments.views import (
    RepaymentListView,
    RepaymentDetailView,
    # RepaymentScheduleView,
    # EarlyRepaymentView,
    # RepaymentReminderView,
)

urlpatterns = [
    # Repayment Management
    path('', RepaymentListView.as_view(), name='repayment_list'),
    path('<uuid:repayment_id>/', RepaymentDetailView.as_view(), name='repayment_detail'),
    
    # # Repayment Scheduling
    # path('schedule/', RepaymentScheduleView.as_view(), name='repayment_schedule'),
    # path('schedule/<uuid:loan_id>/', RepaymentScheduleView.as_view(), name='loan_repayment_schedule'),
    
    # # Early Repayment
    # path('early/', EarlyRepaymentView.as_view(), name='early_repayment'),
    # path('early/<uuid:loan_id>/', EarlyRepaymentView.as_view(), name='loan_early_repayment'),
    
    # # Repayment Reminders
    # path('reminders/', RepaymentReminderView.as_view(), name='repayment_reminders'),
    # path('reminders/settings/', RepaymentReminderView.as_view(), name='repayment_reminder_settings'),
    
    # Overdue Management
     path('overdue/', RepaymentListView.as_view(), name='repayment_overdue'),
     path('overdue/<uuid:loan_id>/restructure/', RepaymentListView.as_view(), name='loan_restructure'),
]
