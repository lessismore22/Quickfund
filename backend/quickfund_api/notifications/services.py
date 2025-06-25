from datetime import timezone
import logging
import requests
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from quickfund_api.notifications.models import Notification, NotificationTemplate
from quickfund_api.utils.exceptions import NotificationError


logger = logging.getLogger(__name__)


class BaseNotificationService:
    """Base class for notification services"""
    
    def __init__(self):
        self.enabled = True
    
    def send(self, recipient: str, message: str, subject: str = None, **kwargs) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement send method")
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement validate_recipient method")


class EmailService(BaseNotificationService):
    """Email notification service"""
    
    def __init__(self):
        super().__init__()
        self.enabled = getattr(settings, 'EMAIL_ENABLED', True)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@quickcash.com')
    
    def send(self, recipient: str, message: str, subject: str = None, 
             template_name: str = None, context: Dict[str, Any] = None, **kwargs) -> bool:
        """Send email notification"""
        if not self.enabled:
            logger.warning("Email service is disabled")
            return False
        
        if not self.validate_recipient(recipient):
            logger.error(f"Invalid email recipient: {recipient}")
            return False
        
        try:
            if template_name and context:
                # Use HTML template
                html_content = render_to_string(f'email/{template_name}.html', context)
                text_content = strip_tags(html_content)
                
                msg = EmailMultiAlternatives(
                    subject=subject or context.get('subject', 'QuickCash Notification'),
                    body=text_content,
                    from_email=self.from_email,
                    to=[recipient]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject or 'QuickCash Notification',
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[recipient],
                    fail_silently=False
                )
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, recipient))
    
    def send_bulk_emails(self, recipients: List[str], message: str, 
                        subject: str = None, template_name: str = None, 
                        context: Dict[str, Any] = None) -> Dict[str, bool]:
        """Send bulk emails"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send(
                recipient=recipient,
                message=message,
                subject=subject,
                template_name=template_name,
                context=context
            )
        return results


class SMSService(BaseNotificationService):
    """SMS notification service using Termii or similar providers"""
    
    def __init__(self):
        super().__init__()
        self.enabled = getattr(settings, 'SMS_ENABLED', True)
        self.api_key = getattr(settings, 'TERMII_API_KEY', '')
        self.sender_id = getattr(settings, 'TERMII_SENDER_ID', 'QuickCash')
        self.base_url = getattr(settings, 'TERMII_BASE_URL', 'https://api.ng.termii.com/api')
    
    def send(self, recipient: str, message: str, subject: str = None, 
             template_name: str = None, context: Dict[str, Any] = None, **kwargs) -> bool:
        """Send SMS notification"""
        if not self.enabled:
            logger.warning("SMS service is disabled")
            return False
        
        if not self.validate_recipient(recipient):
            logger.error(f"Invalid phone number: {recipient}")
            return False
        
        try:
            # Use template if provided
            if template_name and context:
                message = render_to_string(f'sms/{template_name}.txt', context)
            
            payload = {
                "to": recipient,
                "from": self.sender_id,
                "sms": message,
                "type": "plain",
                "api_key": self.api_key,
                "channel": "generic"
            }
            
            response = requests.post(
                f"{self.base_url}/sms/send",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 'ok':
                    logger.info(f"SMS sent successfully to {recipient}")
                    return True
                else:
                    logger.error(f"SMS API error: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"SMS API request failed with status {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"SMS request failed for {recipient}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {str(e)}")
            return False
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format"""
        import re
        # Nigerian phone number pattern
        pattern = r'^\+?234[789][01]\d{8}$|^0[789][01]\d{8}$'
        return bool(re.match(pattern, recipient))
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format phone number to international format"""
        phone_number = phone_number.strip().replace(' ', '').replace('-', '')
        
        if phone_number.startswith('0'):
            return f"+234{phone_number[1:]}"
        elif phone_number.startswith('234'):
            return f"+{phone_number}"
        elif phone_number.startswith('+234'):
            return phone_number
        else:
            return f"+234{phone_number}"


class PushNotificationService(BaseNotificationService):
    """Push notification service for mobile apps"""
    
    def __init__(self):
        super().__init__()
        self.enabled = getattr(settings, 'PUSH_NOTIFICATIONS_ENABLED', False)
        self.fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', '')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
    
    def send(self, recipient: str, message: str, subject: str = None, 
             data: Dict[str, Any] = None, **kwargs) -> bool:
        """Send push notification via FCM"""
        if not self.enabled:
            logger.warning("Push notification service is disabled")
            return False
        
        try:
            payload = {
                "to": recipient,
                "notification": {
                    "title": subject or "QuickCash",
                    "body": message,
                    "sound": "default"
                },
                "data": data or {}
            }
            
            headers = {
                'Authorization': f'key={self.fcm_server_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.fcm_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') == 1:
                    logger.info(f"Push notification sent successfully to {recipient}")
                    return True
                else:
                    logger.error(f"Push notification failed: {result.get('results', [{}])[0].get('error', 'Unknown error')}")
                    return False
            else:
                logger.error(f"FCM request failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send push notification to {recipient}: {str(e)}")
            return False
    
    def validate_recipient(self, recipient: str) -> bool:
        """Validate FCM token format"""
        return len(recipient) > 50  # Basic validation for FCM tokens


class NotificationService:
    """Main notification service that orchestrates different notification types"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
    
    def send_notification(self, notification_type: str, recipient: str, 
                         message: str, subject: str = None, 
                         template_name: str = None, context: Dict[str, Any] = None,
                         priority: str = 'normal', **kwargs) -> bool:
        """Send notification based on type"""
        
        # Create notification record
        notification = Notification.objects.create(
            recipient=recipient,
            message=message,
            subject=subject or 'QuickCash Notification',
            notification_type=notification_type,
            priority=priority,
            status='pending'
        )
        
        success = False
        
        try:
            if notification_type == 'email':
                success = self.email_service.send(
                    recipient=recipient,
                    message=message,
                    subject=subject,
                    template_name=template_name,
                    context=context,
                    **kwargs
                )
            elif notification_type == 'sms':
                # Format phone number for SMS
                formatted_recipient = self.sms_service.format_phone_number(recipient)
                success = self.sms_service.send(
                    recipient=formatted_recipient,
                    message=message,
                    template_name=template_name,
                    context=context,
                    **kwargs
                )
            elif notification_type == 'push':
                success = self.push_service.send(
                    recipient=recipient,
                    message=message,
                    subject=subject,
                    **kwargs
                )
            else:
                logger.error(f"Unknown notification type: {notification_type}")
                notification.status = 'failed'
                notification.error_message = f"Unknown notification type: {notification_type}"
                notification.save()
                return False
            
            # Update notification status
            if success:
                notification.status = 'sent'
                notification.sent_at = timezone.now()
            else:
                notification.status = 'failed'
                notification.error_message = "Failed to send notification"
            
            notification.save()
            return success
            
        except Exception as e:
            logger.error(f"Notification service error: {str(e)}")
            notification.status = 'failed'
            notification.error_message = str(e)
            notification.save()
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        context = {
            'user_name': user_name,
            'app_name': 'QuickCash',
            'subject': 'Welcome to QuickCash!'
        }
        
        return self.send_notification(
            notification_type='email',
            recipient=user_email,
            message=f"Welcome to QuickCash, {user_name}!",
            subject='Welcome to QuickCash!',
            template_name='welcome',
            context=context
        )
    
    def send_loan_approval_notification(self, user_email: str, user_phone: str, 
                                      user_name: str, loan_amount: float, 
                                      loan_id: str) -> Dict[str, bool]:
        """Send loan approval notifications via email and SMS"""
        context = {
            'user_name': user_name,
            'loan_amount': loan_amount,
            'loan_id': loan_id,
            'app_name': 'QuickCash',
            'subject': 'Loan Approved!'
        }
        
        results = {}
        
        # Send email
        results['email'] = self.send_notification(
            notification_type='email',
            recipient=user_email,
            message=f"Congratulations {user_name}! Your loan of ₦{loan_amount:,.2f} has been approved.",
            subject='Loan Approved!',
            template_name='loan_approval',
            context=context
        )
        
        # Send SMS
        results['sms'] = self.send_notification(
            notification_type='sms',
            recipient=user_phone,
            message=f"Congratulations! Your QuickCash loan of ₦{loan_amount:,.2f} has been approved. Loan ID: {loan_id}",
            template_name='loan_approval',
            context=context
        )
        
        return results
    
    def send_loan_rejection_notification(self, user_email: str, user_name: str, 
                                       reason: str = None) -> bool:
        """Send loan rejection notification"""
        context = {
            'user_name': user_name,
            'reason': reason or 'Based on our assessment criteria',
            'app_name': 'QuickCash',
            'subject': 'Loan Application Update'
        }
        
        return self.send_notification(
            notification_type='email',
            recipient=user_email,
            message=f"Dear {user_name}, we regret to inform you that your loan application was not approved.",
            subject='Loan Application Update',
            template_name='loan_rejection',
            context=context
        )
    
    def send_payment_reminder(self, user_email: str, user_phone: str, 
                            user_name: str, amount_due: float, 
                            due_date: str, loan_id: str) -> Dict[str, bool]:
        """Send payment reminder notifications"""
        context = {
            'user_name': user_name,
            'amount_due': amount_due,
            'due_date': due_date,
            'loan_id': loan_id,
            'app_name': 'QuickCash',
            'subject': 'Payment Reminder'
        }
        
        results = {}
        
        # Send email reminder
        results['email'] = self.send_notification(
            notification_type='email',
            recipient=user_email,
            message=f"Dear {user_name}, your loan payment of ₦{amount_due:,.2f} is due on {due_date}.",
            subject='Payment Reminder',
            template_name='payment_reminder',
            context=context
        )
        
        # Send SMS reminder
        results['sms'] = self.send_notification(
            notification_type='sms',
            recipient=user_phone,
            message=f"Payment reminder: ₦{amount_due:,.2f} due on {due_date}. Loan ID: {loan_id}. Pay now to avoid late fees.",
            template_name='payment_reminder',
            context=context
        )
        
        return results


# Service instances
notification_service = NotificationService()
email_service = EmailService()
sms_service = SMSService()
push_service = PushNotificationService()