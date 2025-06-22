import uuid
from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(regex=r'^\+?234[789]\d{9}$', message='Enter a valid Nigerian phone number')]
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    bvn = models.CharField(max_length=11, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    employment_status = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    

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


class Repayment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('ussd', 'USSD'),
        ('virtual_account', 'Virtual Account'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'repayments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Repayment #{str(self.id)[:8]} - ₦{self.amount:,.2f}"
