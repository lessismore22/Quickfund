import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from quickfund_api.users.models import User

class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('defaulted', 'Defaulted'),
    ]
    
    PURPOSE_CHOICES = [
        ('business', 'Business'),
        ('education', 'Education'),
        ('medical', 'Medical'),
        ('personal', 'Personal'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('5000')), MaxValueValidator(Decimal('500000'))]
    )
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))
    tenure_days = models.IntegerField(validators=[MinValueValidator(7), MaxValueValidator(365)])
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credit_score = models.IntegerField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    total_repayment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan #{str(self.id)[:8]} - {self.user.full_name} - ₦{self.amount:,.2f}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date and timezone.now().date() > self.due_date and self.status == 'active'

    def calculate_repayment_amount(self):
        if self.approved_amount:
            principal = self.approved_amount
        else:
            principal = self.amount
        
        interest = principal * (self.interest_rate / 100)
        return principal + interest


class CreditAssessment(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('review', 'Under Review'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='assessment')
    income_verification = models.BooleanField(default=False)
    bank_statement_analysis = models.JSONField(default=dict)
    credit_bureau_check = models.JSONField(default=dict)
    risk_score = models.IntegerField(validators=[MinValueValidator(300), MaxValueValidator(850)])
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    approval_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assessments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'credit_assessments'
