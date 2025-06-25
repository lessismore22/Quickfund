from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, email, first_name):
    """
    Send welcome email to new users
    """
    try:
        subject = 'Welcome to QuickCash!'
        html_message = render_to_string('notifications/email/welcome.html', {
            'first_name': first_name,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Welcome email sent successfully to {email}")
        return True
        
    except Exception as exc:
        logger.error(f"Error sending welcome email to {email}: {str(exc)}")
        self.retry(countdown=60, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_verification_sms(self, phone_number, otp):
    """
    Send verification OTP via SMS
    """
    try:
        from quickfund_api.notifications.services import SMSService
        
        message = f"Your QuickCash verification code is: {otp}. Valid for 5 minutes."
        
        sms_service = SMSService()
        result = sms_service.send_sms(phone_number, message)
        
        if result['success']:
            logger.info(f"Verification SMS sent successfully to {phone_number}")
            return True
        else:
            raise Exception(result['error'])
            
    except Exception as exc:
        logger.error(f"Error sending verification SMS to {phone_number}: {str(exc)}")
        self.retry(countdown=60, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, email, reset_link, first_name):
    """
    Send password reset email
    """
    try:
        subject = 'Reset Your QuickCash Password'
        html_message = render_to_string('registration/password_reset_email.html', {
            'first_name': first_name,
            'reset_link': reset_link,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Password reset email sent successfully to {email}")
        return True
        
    except Exception as exc:
        logger.error(f"Error sending password reset email to {email}: {str(exc)}")
        self.retry(countdown=60, exc=exc)


@shared_task
def cleanup_expired_tokens():
    """
    Clean up expired tokens and verification codes
    """
    try:
        from django.core.cache import cache
        from rest_framework.authtoken.models import Token
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Clean up tokens for inactive users
        inactive_tokens = Token.objects.filter(user__is_active=False)
        deleted_count = inactive_tokens.count()
        inactive_tokens.delete()
        
        logger.info(f"Cleaned up {deleted_count} tokens for inactive users")
        
        # Note: Cache cleanup is automatic based on TTL
        
        return f"Cleaned up {deleted_count} expired tokens"
        
    except Exception as exc:
        logger.error(f"Error cleaning up expired tokens: {str(exc)}")
        raise exc


@shared_task
def update_user_credit_scores():
    """
    Periodic task to update user credit scores
    """
    try:
        from django.contrib.auth import get_user_model
        from quickfund_api.loans.services import CreditScoringService
        
        User = get_user_model()
        scoring_service = CreditScoringService()
        
        # Get verified users who need credit score updates
        users_to_update = User.objects.filter(
            is_verified=True,
            is_active=True
        ).exclude(credit_score__isnull=True)
        
        updated_count = 0
        for user in users_to_update:
            try:
                old_score = user.credit_score
                new_score = scoring_service.recalculate_score(user)
                
                if abs(old_score - new_score) >= 5:  # Only update if significant change
                    user.credit_score = new_score
                    user.save(update_fields=['credit_score'])
                    updated_count += 1
                    
                    logger.info(f"Updated credit score for {user.email}: {old_score} -> {new_score}")
                    
            except Exception as e:
                logger.error(f"Error updating credit score for {user.email}: {str(e)}")
                continue
        
        logger.info(f"Updated credit scores for {updated_count} users")
        return f"Updated credit scores for {updated_count} users"
        
    except Exception as exc:
        logger.error(f"Error in credit score update task: {str(exc)}")
        raise exc


@shared_task
def send_account_verification_reminder():
    """
    Send reminder emails to unverified users
    """
    try:
        from django.contrib.auth import get_user_model
        from datetime import timedelta
        
        User = get_user_model()
        
        # Get users who registered more than 24 hours ago but are not verified
        reminder_date = timezone.now() - timedelta(days=1)
        unverified_users = User.objects.filter(
            is_verified=False,
            is_active=True,
            date_joined__lte=reminder_date,
            verification_reminder_sent=False
        )
        
        sent_count = 0
        for user in unverified_users:
            try:
                subject = 'Verify Your QuickCash Account'
                html_message = render_to_string('notifications/email/verification_reminder.html', {
                    'first_name': user.first_name,
                    'support_email': settings.DEFAULT_FROM_EMAIL,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True
                )
                
                user.verification_reminder_sent = True
                user.save(update_fields=['verification_reminder_sent'])
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Error sending verification reminder to {user.email}: {str(e)}")
                continue
        
        logger.info(f"Sent verification reminders to {sent_count} users")
        return f"Sent verification reminders to {sent_count} users"
        
    except Exception as exc:
        logger.error(f"Error in verification reminder task: {str(exc)}")
        raise exc