from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class NotificationTemplate(models.Model):
    """Template for notifications"""
    
    NOTIFICATION_TYPES = [
        ('welcome', 'Welcome'),
        ('loan_application', 'Loan Application'),
        ('loan_approved', 'Loan Approved'),
        ('loan_rejected', 'Loan Rejected'),
        ('loan_disbursed', 'Loan Disbursed'),
        ('payment_due', 'Payment Due'),
        ('payment_overdue', 'Payment Overdue'),
        ('payment_received', 'Payment Received'),
        ('account_verification', 'Account Verification'),
        ('password_reset', 'Password Reset'),
        ('security_alert', 'Security Alert'),
        ('system_maintenance', 'System Maintenance'),
    ]
    
    CHANNELS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    subject = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    available_variables = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        unique_together = ['notification_type', 'channel']
        ordering = ['notification_type', 'channel']
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_display()})"


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPES = NotificationTemplate.NOTIFICATION_TYPES
    CHANNELS = NotificationTemplate.CHANNELS
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    REFERENCE_TYPES = [
        ('loan', 'Loan'),
        ('payment', 'Payment'),
        ('user', 'User'),
        ('transaction', 'Transaction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read = models.BooleanField(default=False)
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPES, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['notification_type', 'channel']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        if self.status == 'pending':
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at'])
    
    def is_due(self):
        """Check if notification is due for sending"""
        if self.scheduled_at:
            return timezone.now() >= self.scheduled_at
        return True
    
    @property
    def is_overdue(self):
        """Check if notification is overdue"""
        if self.scheduled_at and self.status == 'pending':
            return timezone.now() > self.scheduled_at
        return False


class NotificationLog(models.Model):
    """Log of notification delivery attempts"""
    
    CHANNELS = NotificationTemplate.CHANNELS
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='delivery_logs'
    )
    channel = models.CharField(max_length=20, choices=CHANNELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    provider_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'last_attempt_at']),
        ]
    
    def __str__(self):
        return f"Log for {self.notification.title} via {self.get_channel_display()}"
    
    def can_retry(self):
        """Check if notification can be retried"""
        return self.attempts < self.max_attempts and self.status == 'failed'
    
    def increment_attempts(self):
        """Increment attempt count"""
        self.attempts += 1
        self.last_attempt_at = timezone.now()
        self.save(update_fields=['attempts', 'last_attempt_at'])


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    NOTIFICATION_TYPES = NotificationTemplate.NOTIFICATION_TYPES
    CHANNELS = NotificationTemplate.CHANNELS
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        unique_together = ['user', 'notification_type', 'channel']
        ordering = ['notification_type', 'channel']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_notification_type_display()} via {self.get_channel_display()}"