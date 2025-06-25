import logging
from typing import Dict, Any, List, Optional
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from celery.exceptions import Retry
from quickfund_api.notifications.models import Notification, NotificationTemplate
from quickfund_api.notifications.services import notification_service, email_service, sms_service
from quickfund_api.users.models import CustomUser
from quickfund_api.loans.models import Loan
from quickfund_api.utils.exceptions import NotificationError


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, notification_id: int):
    """
    Celery task to send a notification
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Skip if already sent
        if notification.status == 'sent':
            logger.info(f"Notification {notification_id} already sent")
            return True
        
        # Update status to processing
        notification.status = 'processing'
        notification.save()
        
        success = False
        
        if notification.notification_type == 'email':
            success = email_service.send(
                recipient=notification.recipient,
                message=notification.message,
                subject=notification.subject
            )
        elif notification.notification_type == 'sms':
            success = sms_service.send(
                recipient=notification.recipient,
                message=notification.message
            )
        
        if success:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            logger.info(f"Notification {notification_id} sent successfully")
            return True
        else:
            notification.status = 'failed'
            notification.retry_count += 1
            notification.save()
            
            # Retry if under max retries
            if notification.retry_count < notification.max_retries:
                logger.warning(f"Notification {notification_id} failed, retrying...")
                raise self.retry(countdown=60 * (2 ** notification.retry_count))
            else:
                logger.error(f"Notification {notification_id} failed permanently")
                return False
                
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return False
    except Exception as exc:
        logger.error(f"Error sending notification {notification_id}: {str(exc)}")
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.status = 'failed'
            notification.error_message = str(exc)
            notification.retry_count += 1
            notification.save()
            
            if notification.retry_count < notification.max_retries:
                raise self.retry(exc=exc, countdown=60 * (2 ** notification.retry_count))
        except:
            pass
        return False


@shared_task
def send_bulk_notifications_task(notification_data_list: List[Dict[str, Any]]):
    """
    Celery task to send bulk notifications
    """
    results = []
    
    for notification_data in notification_data_list:
        try:
            # Create notification record
            notification = Notification.objects.create(**notification_data)
            
            # Queue individual notification task
            send_notification_task.delay(notification.id)
            results.append({'id': notification.id, 'status': 'queued'})
            
        except Exception as e:
            logger.error(f"Error creating bulk notification: {str(e)}")
            results.append({'error': str(e), 'status': 'failed'})
    
    return results


@shared_task
def send_welcome_email_task(user_id: int):
    """
    Send welcome email to new user
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        
        success = notification_service.send_welcome_email(
            user_email=user.email,
            user_name=user.get_full_name() or user.username
        )
        
        if success:
            logger.info(f"Welcome email sent to user {user_id}")
        else:
            logger.error(f"Failed to send welcome email to user {user_id}")
        
        return success
        
    except CustomUser.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
        return False
    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {str(e)}")
        return False


@shared_task
def send_loan_approval_notification_task(loan_id: int):
    """
    Send loan approval notifications (email + SMS)
    """
    try:
        loan = Loan.objects.select_related('user').get(id=loan_id)
        user = loan.user
        
        results = notification_service.send_loan_approval_notification(
            user_email=user.email,
            user_phone=user.phone_number,
            user_name=user.get_full_name() or user.username,
            loan_amount=float(loan.amount),
            loan_id=str(loan.id)
        )
        
        logger.info(f"Loan approval notifications sent for loan {loan_id}: {results}")
        return results
        
    except Loan.DoesNotExist:
        logger.error(f"Loan {loan_id} not found for approval notification")
        return False
    except Exception as e:
        logger.error(f"Error sending loan approval notification for loan {loan_id}: {str(e)}")
        return False


@shared_task
def send_loan_rejection_notification_task(loan_id: int, reason: str = None):
    """
    Send loan rejection notification
    """
    try:
        loan = Loan.objects.select_related('user').get(id=loan_id)
        user = loan.user
        
        success = notification_service.send_loan_rejection_notification(
            user_email=user.email,
            user_name=user.get_full_name() or user.username,
            reason=reason
        )
        
        if success:
            logger.info(f"Loan rejection notification sent for loan {loan_id}")
        else:
            logger.error(f"Failed to send loan rejection notification for loan {loan_id}")
        
        return success
        
    except Loan.DoesNotExist:
        logger.error(f"Loan {loan_id} not found for rejection notification")
        return False
    except Exception as e:
        logger.error(f"Error sending loan rejection notification for loan {loan_id}: {str(e)}")
        return False


@shared_task
def send_payment_reminder_task(loan_id: int):
    """
    Send payment reminder notifications
    """
    try:
        loan = Loan.objects.select_related('user').get(id=loan_id)
        user = loan.user
        
        # Calculate amount due and due date
        amount_due = loan.calculate_amount_due()
        due_date = loan.due_date.strftime('%B %d, %Y') if loan.due_date else 'N/A'
        
        results = notification_service.send_payment_reminder(
            user_email=user.email,
            user_phone=user.phone_number,
            user_name=user.get_full_name() or user.username,
            amount_due=float(amount_due),
            due_date=due_date,
            loan_id=str(loan.id)
        )
        
        logger.info(f"Payment reminder sent for loan {loan_id}: {results}")
        return results
        
    except Loan.DoesNotExist:
        logger.error(f"Loan {loan_id} not found for payment reminder")
        return False
    except Exception as e:
        logger.error(f"Error sending payment reminder for loan {loan_id}: {str(e)}")
        return False


@shared_task
def process_failed_notifications_task():
    """
    Process and retry failed notifications
    """
    from quickfund_api.notifications.filters import get_failed_notifications_for_retry
    
    failed_notifications = get_failed_notifications_for_retry(max_age_hours=24)
    processed_count = 0
    
    for notification in failed_notifications:
        try:
            # Queue for retry
            send_notification_task.delay(notification.id)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error queuing failed notification {notification.id} for retry: {str(e)}")
    
    logger.info(f"Queued {processed_count} failed notifications for retry")
    return processed_count


@shared_task
def cleanup_old_notifications_task(days_to_keep: int = 90):
    """
    Clean up old notification records
    """
    cutoff_date = timezone.now() - timedelta(days=days_to_keep)
    
    try:
        # Keep failed notifications for longer (for analysis)
        old_successful_notifications = Notification.objects.filter(
            status='sent',
            created_at__lt=cutoff_date
        )
        
        count = old_successful_notifications.count()
        old_successful_notifications.delete()
        
        logger.info(f"Cleaned up {count} old notification records")
        return count
        
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {str(e)}")
        return 0


@shared_task
def send_daily_payment_reminders_task():
    """
    Send daily payment reminders for loans due soon
    """
    from django.db.models import Q
    
    try:
        # Get loans due in 3 days, 1 day, and overdue
        today = timezone.now().date()
        due_in_3_days = today + timedelta(days=3)
        due_in_1_day = today + timedelta(days=1)
        
        loans_for_reminder = Loan.objects.filter(
            Q(due_date=due_in_3_days) | Q(due_date=due_in_1_day) | Q(due_date__lt=today),
            status__in=['approved', 'active'],
            is_fully_paid=False
        ).select_related('user')
        
        reminder_count = 0
        
        for loan in loans_for_reminder:
            send_payment_reminder_task.delay(loan.id)
            reminder_count += 1
        
        logger.info(f"Queued {reminder_count} payment reminders")
        return reminder_count
        
    except Exception as e:
        logger.error(f"Error sending daily payment reminders: {str(e)}")
        return 0


@shared_task
def send_weekly_loan_summary_task():
    """
    Send weekly loan summary to users with active loans
    """
    try:
        active_loans = Loan.objects.filter(
            status__in=['approved', 'active'],
            is_fully_paid=False
        ).select_related('user')
        
        summary_count = 0
        
        for loan in active_loans:
            user = loan.user
            
            # Calculate loan summary data
            amount_due = loan.calculate_amount_due()
            days_until_due = (loan.due_date - timezone.now().date()).days if loan.due_date else 0
            
            context = {
                'user_name': user.get_full_name() or user.username,
                'loan_amount': float(loan.amount),
                'amount_due': float(amount_due),
                'due_date': loan.due_date.strftime('%B %d, %Y') if loan.due_date else 'N/A',
                'days_until_due': days_until_due,
                'loan_id': str(loan.id),
                'app_name': 'QuickCash',
                'subject': 'Weekly Loan Summary'
            }
            
            success = notification_service.send_notification(
                notification_type='email',
                recipient=user.email,
                message=f"Weekly summary for your QuickCash loan #{loan.id}",
                subject='Weekly Loan Summary',
                template_name='weekly_summary',
                context=context
            )
            
            if success:
                summary_count += 1
        
        logger.info(f"Sent {summary_count} weekly loan summaries")
        return summary_count
        
    except Exception as e:
        logger.error(f"Error sending weekly loan summaries: {str(e)}")
        return 0


@shared_task
def send_notification_with_retry_task(notification_type: str, recipient: str, 
                                    message: str, subject: str = None,
                                    max_retries: int = 3, retry_delay: int = 300):
    """
    Send notification with custom retry logic
    """
    notification = Notification.objects.create(
        recipient=recipient,
        message=message,
        subject=subject or 'QuickCash Notification',
        notification_type=notification_type,
        status='pending',
        max_retries=max_retries
    )
    
    # Queue the notification task
    send_notification_task.apply_async(
        args=[notification.id],
        retry_policy={
            'max_retries': max_retries,
            'interval_start': retry_delay,
            'interval_step': retry_delay,
            'interval_max': retry_delay * 4,
        }
    )
    
    return notification.id


@shared_task
def generate_notification_reports_task():
    """
    Generate daily notification delivery reports
    """
    try:
        from django.db.models import Count, Q
        
        today = timezone.now().date()
        
        # Get today's notification stats
        stats = Notification.objects.filter(
            created_at__date=today
        ).aggregate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending'))
        )
        
        # Calculate delivery rate
        delivery_rate = (stats['sent'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        report_data = {
            'date': today.isoformat(),
            'total_notifications': stats['total'],
            'sent_notifications': stats['sent'],
            'failed_notifications': stats['failed'],
            'pending_notifications': stats['pending'],
            'delivery_rate': round(delivery_rate, 2)
        }
        
        # Log the report (in production, you might save to database or send to monitoring service)
        logger.info(f"Daily notification report: {report_data}")
        
        # Send report to admin if configured
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
        if admin_email and stats['total'] > 0:
            notification_service.send_notification(
                notification_type='email',
                recipient=admin_email,
                subject='QuickCash Daily Notification Report',
                message=f"Daily notification statistics:\n"
                       f"Total: {stats['total']}\n"
                       f"Sent: {stats['sent']}\n"
                       f"Failed: {stats['failed']}\n"
                       f"Pending: {stats['pending']}\n"
                       f"Delivery Rate: {delivery_rate:.2f}%"
            )
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error generating notification reports: {str(e)}")
        return None


@shared_task
def test_notification_services_task():
    """
    Test all notification services (for monitoring/health checks)
    """
    results = {
        'email': False,
        'sms': False,
        'timestamp': timezone.now().isoformat()
    }
    
    test_email = getattr(settings, 'TEST_EMAIL', 'test@quickcash.com')
    test_phone = getattr(settings, 'TEST_PHONE', '+2348000000000')
    
    # Test email service
    try:
        results['email'] = email_service.send(
            recipient=test_email,
            message='Test email from QuickCash notification service',
            subject='Service Test'
        )
    except Exception as e:
        logger.error(f"Email service test failed: {str(e)}")
        results['email_error'] = str(e)
    
    # Test SMS service
    try:
        results['sms'] = sms_service.send(
            recipient=test_phone,
            message='Test SMS from QuickCash notification service'
        )
    except Exception as e:
        logger.error(f"SMS service test failed: {str(e)}")
        results['sms_error'] = str(e)
    
    logger.info(f"Notification service test results: {results}")
    return results


# Periodic task scheduling (to be configured in settings)
# These would typically be configured in your Celery beat schedule

def send_payment_confirmation_task(user_id, payment_data):
    """
    Send payment confirmation notification to user
    
    Args:
        user_id: ID of the user who made the payment
        payment_data: Dictionary containing payment details
    """
    try:
        # Import User model here to avoid circular imports
        from django.contrib.auth.models import User
        
        user = User.objects.get(id=user_id)
        
        # TODO: Implement your notification logic
        # Examples:
        # - Send email confirmation
        # - Send SMS notification  
        # - Create in-app notification
        # - Log the payment confirmation
        
        print(f"Payment confirmation sent to user {user.username}")
        return True
        
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found")
        return False
    except Exception as e:
        print(f"Error sending payment confirmation: {e}")
        return False

def schedule_periodic_tasks():
    """
    Configure periodic tasks for notifications
    This would be called in your Celery configuration
    """
    from celery.schedules import crontab
    
    return {
        'process-failed-notifications': {
            'task': 'apps.notifications.tasks.process_failed_notifications_task',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
        },
        'daily-payment-reminders': {
            'task': 'apps.notifications.tasks.send_daily_payment_reminders_task',
            'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
        },
        'weekly-loan-summaries': {
            'task': 'apps.notifications.tasks.send_weekly_loan_summary_task',
            'schedule': crontab(hour=10, minute=0, day_of_week=1),  # Monday at 10 AM
        },
        'cleanup-old-notifications': {
            'task': 'apps.notifications.tasks.cleanup_old_notifications_task',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday at 2 AM
        },
        'generate-notification-reports': {
            'task': 'apps.notifications.tasks.generate_notification_reports_task',
            'schedule': crontab(hour=23, minute=30),  # Daily at 11:30 PM
        },
        'test-notification-services': {
            'task': 'apps.notifications.tasks.test_notification_services_task',
            'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
        },
    }