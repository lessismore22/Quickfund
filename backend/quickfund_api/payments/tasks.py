"""
Celery tasks for payment processing and related operations.
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Sum

from .models import PaymentTransaction, Repayment
from .services import payment_service
from apps.loans.models import Loan
from apps.users.models import User
from apps.notifications.tasks import (
    send_payment_reminder_task,
    send_payment_failed_task,
    send_overdue_payment_task
)
from utils.exceptions import PaymentProcessingError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_pending_payments(self):
    """
    Process pending payment transactions.
    Check status with payment providers and update accordingly.
    """
    try:
        # Get pending transactions older than 10 minutes
        cutoff_time = timezone.now() - timedelta(minutes=10)
        pending_transactions = PaymentTransaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        processed_count = 0
        failed_count = 0
        
        for transaction in pending_transactions[:100]:  # Process in batches
            try:
                # Verify payment status
                result = payment_service.verify_payment(
                    transaction.reference,
                    transaction.provider
                )
                
                if result.get('status') == 'success':
                    processed_count += 1
                    logger.info(f"Payment verified: {transaction.reference}")
                else:
                    failed_count += 1
                    logger.warning(f"Payment failed: {transaction.reference}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Failed to verify payment {transaction.reference}: {str(e)}"
                )
        
        logger.info(
            f"Processed {processed_count} payments, "
            f"{failed_count} failed verifications"
        )
        
        return {
            'processed': processed_count,
            'failed': failed_count,
            'total_checked': pending_transactions.count()
        }
        
    except Exception as e:
        logger.error(f"Failed to process pending payments: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_transactions(self):
    """
    Clean up expired payment transactions.
    Mark transactions as expired if not completed within timeout period.
    """
    try:
        # Get transactions older than the timeout period
        timeout_hours = getattr(settings, 'PAYMENT_TIMEOUT_HOURS', 24)
        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)
        
        expired_transactions = PaymentTransaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        count = expired_transactions.update(
            status='expired',
            failure_reason='Transaction timeout'
        )
        
        logger.info(f"Marked {count} transactions as expired")
        
        return {'expired_count': count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired transactions: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def send_payment_reminders(self):
    """
    Send payment reminders for upcoming and overdue payments.
    """
    try:
        today = timezone.now().date()
        
        # Get loans with upcoming payments (3 days before due date)
        upcoming_date = today + timedelta(days=3)
        overdue_date = today - timedelta(days=1)
        
        # Find loans with upcoming payments
        upcoming_loans = Loan.objects.filter(
            status='active',
            repayment_schedule__contains=[upcoming_date.isoformat()]
        ).select_related('borrower')
        
        # Find overdue loans
        overdue_loans = Loan.objects.filter(
            status='active',
            outstanding_amount__gt=0
        ).select_related('borrower')
        
        reminder_count = 0
        overdue_count = 0
        
        # Send upcoming payment reminders
        for loan in upcoming_loans:
            try:
                # Check if reminder already sent today
                if not hasattr(loan, '_reminder_sent_today'):
                    send_payment_reminder_task.delay(
                        user_id=str(loan.borrower.id),
                        loan_id=str(loan.id),
                        reminder_type='upcoming'
                    )
                    reminder_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send reminder for loan {loan.id}: {str(e)}")
        
        # Send overdue payment notifications
        for loan in overdue_loans:
            try:
                # Check if any payment is overdue
                if self._is_loan_overdue(loan):
                    send_overdue_payment_task.delay(
                        user_id=str(loan.borrower.id),
                        loan_id=str(loan.id)
                    )
                    overdue_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send overdue notice for loan {loan.id}: {str(e)}")
        
        logger.info(
            f"Sent {reminder_count} payment reminders and "
            f"{overdue_count} overdue notifications"
        )
        
        return {
            'reminders_sent': reminder_count,
            'overdue_notifications': overdue_count
        }
        
    except Exception as e:
        logger.error(f"Failed to send payment reminders: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def reconcile_payments(self, date_str=None):
    """
    Reconcile payments with payment provider records.
    
    Args:
        date_str: Date to reconcile in YYYY-MM-DD format (defaults to yesterday)
    """
    try:
        if date_str:
            reconcile_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            reconcile_date = (timezone.now() - timedelta(days=1)).date()
        
        # Get completed transactions for the date
        transactions = PaymentTransaction.objects.filter(
            status='completed',
            completed_at__date=reconcile_date
        )
        
        reconciled_count = 0
        discrepancy_count = 0
        
        for transaction in transactions:
            try:
                # Verify with provider
                provider_data = payment_service.verify_payment(
                    transaction.reference,
                    transaction.provider
                )
                
                # Check for discrepancies
                provider_amount = Decimal(str(provider_data.get('amount', 0))) / 100
                if abs(provider_amount - transaction.amount) > Decimal('0.01'):
                    logger.warning(
                        f"Amount discrepancy for {transaction.reference}: "
                        f"Local: {transaction.amount}, Provider: {provider_amount}"
                    )
                    discrepancy_count += 1
                else:
                    reconciled_count += 1
                    
            except Exception as e:
                logger.error(f"Reconciliation failed for {transaction.reference}: {str(e)}")
                discrepancy_count += 1
        
        logger.info(
            f"Reconciled {reconciled_count} transactions, "
            f"{discrepancy_count} discrepancies found for {reconcile_date}"
        )
        
        return {
            'date': reconcile_date.isoformat(),
            'reconciled': reconciled_count,
            'discrepancies': discrepancy_count,
            'total_transactions': transactions.count()
        }
        
    except Exception as e:
        logger.error(f"Payment reconciliation failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def process_failed_payment_retries(self):
    """
    Process automatic retries for failed payments.
    """
    try:
        # Get failed transactions eligible for retry
        cutoff_time = timezone.now() - timedelta(hours=1)
        failed_transactions = PaymentTransaction.objects.filter(
            status='failed',
            created_at__gt=cutoff_time,
            retry_count__lt=3
        )
        
        retry_count = 0
        
        for transaction in failed_transactions:
            try:
                # Attempt to reverify the payment
                result = payment_service.verify_payment(
                    transaction.reference,
                    transaction.provider
                )
                
                # Update retry count
                transaction.retry_count += 1
                transaction.save()
                
                if result.get('status') == 'success':
                    logger.info(f"Payment retry successful: {transaction.reference}")
                    retry_count += 1
                else:
                    logger.info(f"Payment retry still failed: {transaction.reference}")
                    
            except Exception as e:
                logger.error(f"Retry failed for {transaction.reference}: {str(e)}")
        
        return {'retried_transactions': retry_count}
        
    except Exception as e:
        logger.error(f"Failed payment retry processing failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def generate_payment_reports(self, report_type='daily', date_str=None):
    """
    Generate payment reports for analytics and monitoring.
    
    Args:
        report_type: Type of report ('daily', 'weekly', 'monthly')
        date_str: Date for report in YYYY-MM-DD format
    """
    try:
        if date_str:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            report_date = timezone.now().date()
        
        if report_type == 'daily':
            start_date = report_date
            end_date = report_date + timedelta(days=1)
        elif report_type == 'weekly':
            start_date = report_date - timedelta(days=report_date.weekday())
            end_date = start_date + timedelta(days=7)
        elif report_type == 'monthly':
            start_date = report_date.replace(day=1)
            next_month = (start_date + timedelta(days=32)).replace(day=1)
            end_date = next_month
        else:
            raise ValueError(f"Invalid report type: {report_type}")
        
        # Generate payment statistics
        transactions = PaymentTransaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lt=end_date
        )
        
        stats = {
            'period': f"{start_date} to {end_date - timedelta(days=1)}",
            'total_transactions': transactions.count(),
            'successful_transactions': transactions.filter(status='completed').count(),
            'failed_transactions': transactions.filter(status='failed').count(),
            'pending_transactions': transactions.filter(status='pending').count(),
            'total_amount': transactions.filter(status='completed').aggregate(
                total=Sum('amount'))['total'] or Decimal('0'),
            'average_amount': Decimal('0'),
            'by_provider': {},
        }
        
        if stats['successful_transactions'] > 0:
            stats['average_amount'] = stats['total_amount'] / stats['successful_transactions']
        
        # Group by provider
        for provider in ['paystack']:
            provider_transactions = transactions.filter(provider=provider)
            stats['by_provider'][provider] = {
                'total': provider_transactions.count(),
                'successful': provider_transactions.filter(status='completed').count(),
                'amount': provider_transactions.filter(status='completed').aggregate(
                    total=Sum('amount'))['total'] or Decimal('0'),
            }
        
        logger.info(f"Generated {report_type} payment report for {report_date}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Payment report generation failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


@shared_task(bind=True, max_retries=3)
def update_loan_payment_status(self):
    """
    Update loan payment status based on repayment schedule.
    """
    try:
        today = timezone.now().date()
        updated_count = 0
        
        # Get active loans
        active_loans = Loan.objects.filter(status='active')
        
        for loan in active_loans:
            try:
                # Get total repayments
                total_repaid = Repayment.objects.filter(
                    loan=loan,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                # Update loan repayment status
                if total_repaid != loan.total_repaid:
                    loan.total_repaid = total_repaid
                    loan.outstanding_amount = loan.amount - total_repaid
                    
                    # Check if fully repaid
                    if loan.outstanding_amount <= 0:
                        loan.status = 'paid'
                        loan.repayment_date = timezone.now()
                    
                    loan.save()
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to update loan {loan.id}: {str(e)}")
        
        logger.info(f"Updated payment status for {updated_count} loans")
        
        return {'updated_loans': updated_count}
        
    except Exception as e:
        logger.error(f"Loan payment status update failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)


def _is_loan_overdue(loan):
    """Check if a loan has overdue payments."""
    if not loan.repayment_schedule:
        return False
    
    today = timezone.now().date()
    
    # Get paid amounts by date
    repayments = Repayment.objects.filter(
        loan=loan,
        status='completed'
    ).values_list('payment_date', 'amount')
    
    paid_by_date = {}
    for payment_date, amount in repayments:
        date_key = payment_date.date() if hasattr(payment_date, 'date') else payment_date
        paid_by_date[date_key] = paid_by_date.get(date_key, Decimal('0')) + amount
    
    # Check each scheduled payment
    for scheduled_date_str in loan.repayment_schedule:
        scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        
        if scheduled_date < today:
            paid_amount = paid_by_date.get(scheduled_date, Decimal('0'))
            if paid_amount < loan.monthly_payment_amount:
                return True
    
    return False