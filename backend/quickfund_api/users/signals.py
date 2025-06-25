from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.utils import timezone
import logging

from .models import CustomUser
from quickfund_api.notifications.tasks import send_welcome_email

# Configure logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to handle user creation tasks
    """
    if created:
        # Log user creation
        logger.info(f"New user created: {instance.email}")
        
        # Send welcome email if not already sent
        if not instance.welcome_email_sent:
            send_welcome_email.delay(instance.email, instance.first_name)
            instance.welcome_email_sent = True
            instance.save(update_fields=['welcome_email_sent'])


@receiver(pre_save, sender=CustomUser)
def update_user_profile(sender, instance, **kwargs):
    """
    Signal to handle user profile updates
    """
    if instance.pk:  # Only for existing users
        try:
            old_instance = CustomUser.objects.get(pk=instance.pk)
            
            # Check if user was just verified
            if not old_instance.is_verified and instance.is_verified:
                logger.info(f"User verified: {instance.email}")
                instance.verification_date = timezone.now()
                
                # Clear any verification-related cache
                cache.delete(f'verification_otp_{instance.id}')
            
            # Check if user was deactivated
            if old_instance.is_active and not instance.is_active:
                logger.warning(f"User deactivated: {instance.email}")
                
                # Clear user sessions/tokens
                from rest_framework.authtoken.models import Token
                Token.objects.filter(user=instance).delete()
            
            # Check if user was reactivated
            if not old_instance.is_active and instance.is_active:
                logger.info(f"User reactivated: {instance.email}")
                
        except CustomUser.DoesNotExist:
            pass


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Signal to handle user login
    """
    logger.info(f"User logged in: {user.email}")
    
    # Update last login time
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Clear failed login attempts
    cache.delete(f'failed_login_attempts_{user.email}')


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Signal to handle user logout
    """
    if user:
        logger.info(f"User logged out: {user.email}")


@receiver(post_save, sender=CustomUser)
def update_credit_score(sender, instance, created, **kwargs):
    """
    Signal to update credit score when user is verified
    """
    if not created and instance.is_verified and not instance.credit_score:
        # Calculate initial credit score based on user data
        from quickfund_api.loans.services import CreditScoringService
        
        try:
            scoring_service = CreditScoringService()
            credit_score = scoring_service.calculate_initial_score(instance)
            
            if credit_score != instance.credit_score:
                instance.credit_score = credit_score
                instance.save(update_fields=['credit_score'])
                logger.info(f"Credit score updated for user {instance.email}: {credit_score}")
                
        except Exception as e:
            logger.error(f"Error updating credit score for user {instance.email}: {str(e)}")


@receiver(post_save, sender=CustomUser)
def user_activity_log(sender, instance, created, **kwargs):
    """
    Signal to log user activity
    """
    if created:
        # Log new user registration
        logger.info(f"User activity: New registration - {instance.email}")
    else:
        # Log user updates
        logger.info(f"User activity: Profile updated - {instance.email}")