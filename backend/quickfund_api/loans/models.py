from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class LoanType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_term_months = models.PositiveIntegerField(default=1)
    max_term_months = models.PositiveIntegerField(default=60)
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]

    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    loan_id = models.CharField(max_length=20, unique=True, blank=True)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveIntegerField()
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    purpose = models.TextField(blank=True)
    
    # Dates
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    disbursement_date = models.DateTimeField(blank=True, null=True)
    first_payment_date = models.DateField(blank=True, null=True)
    maturity_date = models.DateField(blank=True, null=True)
    
    # Additional fields
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.loan_id:
            # Generate loan ID
            import uuid
            self.loan_id = f"LN{str(uuid.uuid4().hex[:8]).upper()}"
        
        if self.principal_amount and self.interest_rate and self.term_months:
            # Calculate monthly payment using loan formula
            monthly_rate = self.interest_rate / Decimal('100') / Decimal('12')
            if monthly_rate > 0:
                payment = (self.principal_amount * monthly_rate * 
                          (1 + monthly_rate) ** self.term_months) / \
                          ((1 + monthly_rate) ** self.term_months - 1)
                self.monthly_payment = payment.quantize(Decimal('0.01'))
                self.total_amount = self.monthly_payment * self.term_months
            else:
                self.monthly_payment = self.principal_amount / self.term_months
                self.total_amount = self.principal_amount
        
        if not self.outstanding_balance:
            self.outstanding_balance = self.principal_amount
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_id} - {self.borrower.get_full_name() or self.borrower.username}"

    class Meta:
        ordering = ['-application_date']


class LoanPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('regular', 'Regular Payment'),
        ('early', 'Early Payment'),
        ('penalty', 'Penalty Payment'),
        ('late_fee', 'Late Fee'),
    ]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=20, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='regular')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            import uuid
            self.payment_id = f"PY{str(uuid.uuid4().hex[:8]).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_id} - {self.loan.loan_id}"

    class Meta:
        ordering = ['due_date']

class CreditAssessment(models.Model):
    ...
    pass

class LoanApplication(models.Model):
    # adjust according to your needs

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaid', 'Repaid'),
    ]
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('education', 'Education Loan'),
        ('auto', 'Auto Loan'),
        ('mortgage', 'Mortgage'),
    ]
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Application #{self.id} - {self.applicant.username}"