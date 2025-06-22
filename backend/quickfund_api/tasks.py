from celery import shared_task
from .services import LoanProcessingService

@shared_task
def process_loan_application(loan_id):
    """Process loan application asynchronously"""
    service = LoanProcessingService()
    service.process_loan_application(loan_id)


# apps/notifications/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from .services import SMSService, EmailService

User = get_user_model()

@shared_task
def send_welcome_notification(user_id):
    """Send welcome notification to new user"""
    try:
        user = User.objects.get(id=user_id)
        
        # Send SMS
        sms_service = SMSService()
        sms_service.send_welcome_sms(user.phone, user.first_name)
        
        # Send Email
        email_service = EmailService()
        email_service.send_welcome_email(user.email, user.first_name)
        
    except User.DoesNotExist:
        pass

@shared_task
def send_loan_approval_notification(loan_id):
    """Send loan approval notification"""
    from .models import Loan
    
    try:
        loan = Loan.objects.get(id=loan_id)
        
        # Send SMS
        sms_service = SMSService()
        sms_service.send_loan_approval_sms(loan)
        
        # Send Email
        email_service = EmailService()
        email_service.send_loan_approval_email(loan)
        
    except Loan.DoesNotExist:
        pass