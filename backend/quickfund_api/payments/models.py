from decimal import Decimal
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from ..utils.constants import PAYMENT_STATUS_CHOICES, PAYMENT_METHOD_CHOICES

User = get_user_model()

class PaymentTransaction(models.Model):
    """
    Represents a payment transaction in the system
    """
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('fee', 'Fee'),
        ('interest', 'Interest'),
        ('penalty', 'Penalty'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Basic transaction info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Reference and tracking
    reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Optional: Link to a loan if this transaction is loan-related
    # loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, null=True, blank=True)
    
    # Payment method used
    # payment_method = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['created_at']),
        ]

# For Transaction model (aliased to PaymentTransaction)
Transaction = PaymentTransaction


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('fee', 'Fee'),
        ('interest', 'Interest'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Link to a loan if this transaction is loan-related
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"
    
    class Meta:
        ordering = ['-created_at']


class PaymentGateway(models.Model):
    """Model for payment gateway configurations"""
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    public_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    webhook_url = models.URLField(blank=True)
    test_mode = models.BooleanField(default=True)
    supported_currencies = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_gateways'
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'

    def __str__(self):
        return f"{self.name} ({'Test' if self.test_mode else 'Live'})"


class PaymentMethod(models.Model):
    """Model for user payment methods"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    token = models.CharField(max_length=255, unique=True)  # Gateway token
    last_four = models.CharField(max_length=4, blank=True)  # Last 4 digits for cards
    expiry_month = models.IntegerField(null=True, blank=True)
    expiry_year = models.IntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_payment_method'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_method_type_display()} ({self.last_four})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default payment method per user
            PaymentMethod.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Model for payment transactions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    repayment = models.ForeignKey('Repayment', on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='NGN')
    description = models.TextField(blank=True)
    
    # Gateway information
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    gateway_reference = models.CharField(max_length=255, unique=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(blank=True)
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Fees and charges
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway_reference']),
            models.Index(fields=['initiated_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.gateway_reference} - {self.amount} {self.currency}"

    @property
    def is_successful(self):
        return self.status == 'successful'

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_failed(self):
        return self.status == 'failed'

    @property
    def net_amount(self):
        """Amount after deducting fees"""
        return self.amount - self.gateway_fee - self.processing_fee

    def mark_as_successful(self, gateway_response=None):
        """Mark payment as successful"""
        self.status = 'successful'
        self.confirmed_at = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()

    def mark_as_failed(self, reason=None, gateway_response=None):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        if reason:
            self.failure_reason = reason
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()


class Repayment(models.Model):
    """Model for loan repayments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey('loans.Loan', on_delete=models.CASCADE, related_name='repayments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repayments')
    
    # Repayment details
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Due date and payment date
    due_date = models.DateField()
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
            ('written_off', 'Written Off'),
        ],
        default='pending'
    )
    
    # Payment tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'repayments'
        verbose_name = 'Repayment'
        verbose_name_plural = 'Repayments'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['loan', 'due_date']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Repayment for {self.loan} - {self.amount} due {self.due_date}"

    @property
    def is_overdue(self):
        """Check if repayment is overdue"""
        if self.status == 'paid':
            return False
        return timezone.now().date() > self.due_date

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def outstanding_amount(self):
        """Calculate outstanding amount"""
        return self.amount + self.late_fee - self.amount_paid

    def apply_payment(self, amount):
        """Apply payment to this repayment"""
        if amount <= 0:
            return False
        
        remaining_amount = min(amount, self.outstanding_amount)
        self.amount_paid += remaining_amount
        
        if self.amount_paid >= (self.amount + self.late_fee):
            self.status = 'paid'
            self.paid_date = timezone.now()
        elif self.amount_paid > 0:
            self.status = 'partial'
        
        self.save()
        return remaining_amount

    def calculate_late_fee(self, rate=0.05):
        """Calculate late fee based on days overdue"""
        if not self.is_overdue or self.status == 'paid':
            return 0
        
        days_overdue = self.days_overdue
        if days_overdue > 0:
            # 5% of outstanding amount per 30 days
            late_fee = (self.outstanding_amount * rate * days_overdue) / 30
            return round(late_fee, 2)
        return 0


class PaymentRefund(models.Model):
    """Model for payment refunds"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reason = models.TextField()
    
    # Gateway information
    gateway_reference = models.CharField(max_length=255, unique=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('successful', 'Successful'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='refund_requests')
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'payment_refunds'
        verbose_name = 'Payment Refund'
        verbose_name_plural = 'Payment Refunds'
        ordering = ['-requested_at']

    def __str__(self):
        return f"Refund {self.gateway_reference} - {self.amount}"

    def mark_as_successful(self):
        """Mark refund as successful"""
        self.status = 'successful'
        self.processed_at = timezone.now()
        self.save()

    def mark_as_failed(self):
        """Mark refund as failed"""
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.save()


class PaymentWebhook(models.Model):
    """Model for storing payment webhook events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=255, unique=True)
    payload = models.JSONField()
    
    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    
    # Related payment if identified
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'payment_webhooks'
        verbose_name = 'Payment Webhook'
        verbose_name_plural = 'Payment Webhooks'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['gateway', 'event_type']),
            models.Index(fields=['processed', 'received_at']),
        ]

    def __str__(self):
        return f"Webhook {self.event_type} - {self.gateway.name}"

    def mark_as_processed(self, payment=None):
        """Mark webhook as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        if payment:
            self.payment = payment
        self.save()

    def mark_as_failed(self, error_message):
        """Mark webhook processing as failed"""
        self.error_message = error_message
        self.save()