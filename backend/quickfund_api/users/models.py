from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class CustomUser(AbstractUser):
    """Custom User model with additional fields for micro-lending"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('E', 'Employed'),
        ('SE', 'Self-Employed'),
        ('U', 'Unemployed'),
        ('R', 'Retired'),
        ('S', 'Student'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal Information
    phone_number = PhoneNumberField(unique=True, help_text="Phone number with country code")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, blank=True)
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    
    # Employment Information
    employment_status = models.CharField(max_length=2, choices=EMPLOYMENT_STATUS_CHOICES, blank=True)
    employer_name = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    work_phone = PhoneNumberField(blank=True)
    
    # Bank Information
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    
    # KYC Information
    bvn_validator = RegexValidator(
        regex=r'^\d{11}$',
        message="BVN must be exactly 11 digits"
    )
    bvn = models.CharField(
        max_length=11, 
        validators=[bvn_validator], 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Bank Verification Number (BVN)"
    )
    bvn_verified = models.BooleanField(default=False)
    nin = models.CharField(max_length=11, blank=True, help_text="National Identification Number")
    
    # Profile Management
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_profile_complete = models.BooleanField(default=False)
    kyc_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Credit Information
    credit_score = models.IntegerField(default=0, help_text="Credit score (0-850)")
    total_loans_taken = models.IntegerField(default=0)
    total_amount_borrowed = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount_repaid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    default_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        required_fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'gender', 'address_line_1', 'city', 
            'state', 'employment_status', 'monthly_income', 'bvn'
        ]
        
        completed_fields = 0
        for field in required_fields:
            if getattr(self, field):
                completed_fields += 1
        
        return (completed_fields / len(required_fields)) * 100
    
    def update_credit_score(self):
        """Update credit score based on loan history"""
        from quickfund_api.loans.models import Loan
        
        loans = Loan.objects.filter(borrower=self)
        
        if not loans.exists():
            self.credit_score = 500  # Default score for new users
        else:
            # Simple credit scoring algorithm
            base_score = 500
            
            # Positive factors
            completed_loans = loans.filter(status='COMPLETED').count()
            base_score += completed_loans * 50
            
            # Negative factors
            defaulted_loans = loans.filter(status='DEFAULTED').count()
            base_score -= defaulted_loans * 100
            
            # Payment history factor
            if self.total_amount_borrowed > 0:
                repayment_rate = (self.total_amount_repaid / self.total_amount_borrowed) * 100
                if repayment_rate >= 95:
                    base_score += 100
                elif repayment_rate >= 80:
                    base_score += 50
                elif repayment_rate < 50:
                    base_score -= 150
            
            # Income factor
            if self.monthly_income:
                if self.monthly_income >= 100000:  # 100k+
                    base_score += 50
                elif self.monthly_income >= 50000:  # 50k+
                    base_score += 25
            
            # Cap the score between 300 and 850
            self.credit_score = max(300, min(850, base_score))
        
        self.save(update_fields=['credit_score'])
    
    def can_apply_for_loan(self):
        """Check if user can apply for a loan"""
        if not self.kyc_verified:
            return False, "KYC verification required"
        
        if not self.is_profile_complete:
            return False, "Profile completion required"
        
        if self.credit_score < 400:
            return False, "Credit score too low"
        
        # Check for active loans
        from quickfund_api.loans.models import Loan
        active_loans = Loan.objects.filter(
            borrower=self, 
            status__in=['PENDING', 'APPROVED', 'DISBURSED']
        ).count()
        
        if active_loans > 0:
            return False, "You have an active loan application or loan"
        
        return True, "Eligible for loan application"
    
    def save(self, *args, **kwargs):
        # Check profile completion
        required_fields = ['first_name', 'last_name', 'phone_number', 'bvn']
        self.is_profile_complete = all(
            getattr(self, field) for field in required_fields
        ) and self.bvn_verified
        
        super().save(*args, **kwargs)


class UserDocument(models.Model):
    """Model for storing user documents"""
    
    DOCUMENT_TYPES = [
        ('ID', 'Government ID'),
        ('PASSPORT', 'International Passport'),
        ('UTILITY', 'Utility Bill'),
        ('INCOME', 'Income Statement'),
        ('BANK', 'Bank Statement'),
        ('OTHER', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='verified_documents'
    )
    
    class Meta:
        db_table = 'user_documents'
        verbose_name = 'User Document'
        verbose_name_plural = 'User Documents'
        unique_together = ['user', 'document_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"