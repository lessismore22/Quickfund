from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Loan, LoanApplication
from ..notifications.tasks import send_loan_notification
from ..payments.models import Repayment
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=LoanApplication)
def handle_loan_application_created(sender, instance, created, **kwargs):
    """
    Handle loan application creation - trigger credit scoring and notifications
    """
    if created:
        logger.info(f"New loan application created: {instance.id}")
        
        # Import here to avoid circular imports
        from .tasks import process_credit_scoring
        
        # Trigger credit scoring task
        process_credit_scoring.delay(instance.id)
        
        # Send application received notification
        send_loan_notification.delay(
            user_id=instance.user.id,
            notification_type='application_received',
            loan_application_id=instance.id
        )


@receiver(post_save, sender=LoanApplication)
def handle_loan_application_status_change(sender, instance, created, **kwargs):
    """
    Handle loan application status changes
    """
    if not created and instance.tracker.has_changed('status'):
        previous_status = instance.tracker.previous('status')
        current_status = instance.status
        
        logger.info(f"Loan application {instance.id} status changed from {previous_status} to {current_status}")
        
        # Handle approval
        if current_status == 'approved':
            # Create loan record
            loan = Loan.objects.create(
                user=instance.user,
                application=instance,
                amount=instance.amount,
                interest_rate=instance.interest_rate,
                term_months=instance.term_months,
                status='active'
            )
            
            # Send approval notification
            send_loan_notification.delay(
                user_id=instance.user.id,
                notification_type='loan_approved',
                loan_id=loan.id
            )
            
        # Handle rejection
        elif current_status == 'rejected':
            send_loan_notification.delay(
                user_id=instance.user.id,
                notification_type='loan_rejected',
                loan_application_id=instance.id
            )


@receiver(post_save, sender=Loan)
def handle_loan_created(sender, instance, created, **kwargs):
    """
    Handle loan creation - set up repayment schedule
    """
    if created:
        logger.info(f"New loan created: {instance.id}")
        
        # Import here to avoid circular imports
        from .tasks import setup_repayment_schedule
        
        # Set up repayment schedule
        setup_repayment_schedule.delay(instance.id)


@receiver(post_save, sender=Loan)
def handle_loan_status_change(sender, instance, created, **kwargs):
    """
    Handle loan status changes
    """
    if not created and instance.tracker.has_changed('status'):
        previous_status = instance.tracker.previous('status')
        current_status = instance.status
        
        logger.info(f"Loan {instance.id} status changed from {previous_status} to {current_status}")
        
        if current_status == 'defaulted':
            # Send default notification
            send_loan_notification.delay(
                user_id=instance.user.id,
                notification_type='loan_defaulted',
                loan_id=instance.id
            )
        elif current_status == 'completed':
            # Send completion notification
            send_loan_notification.delay(
                user_id=instance.user.id,
                notification_type='loan_completed',
                loan_id=instance.id
            )


@receiver(post_save, sender=Repayment)
def handle_repayment_created(sender, instance, created, **kwargs):
    """
    Handle repayment creation - update loan balance and status
    """
    if created and instance.status == 'completed':
        logger.info(f"New repayment completed: {instance.id}")
        
        loan = instance.loan
        
        # Update loan balance
        loan.balance -= instance.amount
        
        # Check if loan is fully paid
        if loan.balance <= 0:
            loan.status = 'completed'
            loan.balance = 0
        
        loan.save()
        
        # Send payment confirmation
        send_loan_notification.delay(
            user_id=loan.user.id,
            notification_type='payment_received',
            loan_id=loan.id,
            repayment_id=instance.id
        )


@receiver(pre_save, sender=Loan)
def calculate_loan_balance(sender, instance, **kwargs):
    """
    Calculate loan balance before saving
    """
    if not instance.pk:  # New loan
        # Calculate total amount with interest
        principal = instance.amount
        monthly_rate = instance.interest_rate / 100 / 12
        term_months = instance.term_months
        
        if monthly_rate > 0:
            # Calculate monthly payment using compound interest formula
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                            ((1 + monthly_rate) ** term_months - 1)
            instance.balance = monthly_payment * term_months
        else:
            # No interest
            instance.balance = principal
        
        instance.monthly_payment = instance.balance / term_months


@receiver(post_save, sender=User)
def handle_user_profile_update(sender, instance, created, **kwargs):
    """
    Handle user profile updates that might affect credit scoring
    """
    if not created and hasattr(instance, 'tracker'):
        # Check if credit-relevant fields have changed
        credit_fields = ['income', 'employment_status', 'phone_verified', 'email_verified']
        
        if any(instance.tracker.has_changed(field) for field in credit_fields if hasattr(instance, field)):
            logger.info(f"Credit-relevant fields updated for user {instance.id}")
            
            # Update credit score for pending applications
            pending_applications = LoanApplication.objects.filter(
                user=instance,
                status='pending'
            )
            
            for application in pending_applications:
                from .tasks import update_credit_score
                update_credit_score.delay(application.id)