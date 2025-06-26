from django import forms
from decimal import Decimal
from .models import Payment


class PaymentInitiationForm(forms.Form):
    """Form for initiating payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
    ]
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01'
        })
    )
    
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Payment description (optional)'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial='paystack',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        if amount > Decimal('1000000.00'):  # 1 million limit
            raise forms.ValidationError("Amount cannot exceed ₦1,000,000")
        return amount


class LoanRepaymentForm(forms.Form):
    """Form for loan repayments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
    ]
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('1.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter repayment amount',
            'step': '0.01'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        initial='paystack',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        super().__init__(*args, **kwargs)
        
        if self.loan:
            # Set minimum amount based on loan
            self.fields['amount'].min_value = self.loan.minimum_payment_amount
            self.fields['amount'].widget.attrs['min'] = str(self.loan.minimum_payment_amount)
            self.fields['amount'].help_text = f"Minimum payment: ₦{self.loan.minimum_payment_amount}"
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        
        if self.loan:
            if amount < self.loan.minimum_payment_amount:
                raise forms.ValidationError(
                    f"Amount must be at least ₦{self.loan.minimum_payment_amount}"
                )
            
            if amount > self.loan.outstanding_balance:
                raise forms.ValidationError(
                    f"Amount cannot exceed outstanding balance of ₦{self.loan.outstanding_balance}"
                )
        
        return amount


class PaymentFilterForm(forms.Form):
    """Form for filtering payment history"""
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('', 'All Methods'),
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
        ('wallet', 'Wallet'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date must be before end date")
        
        return cleaned_data


class RefundRequestForm(forms.Form):
    """Form for requesting payment refunds"""
    
    REFUND_REASON_CHOICES = [
        ('duplicate', 'Duplicate Payment'),
        ('service_not_received', 'Service Not Received'),
        ('technical_error', 'Technical Error'),
        ('cancelled_order', 'Cancelled Order'),
        ('other', 'Other'),
    ]
    
    reason = forms.ChoiceField(
        choices=REFUND_REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide additional details about your refund request'
        }),
        max_length=500,
        help_text="Maximum 500 characters"
    )
    
    def clean_description(self):
        description = self.cleaned_data['description']
        if len(description.strip()) < 10:
            raise forms.ValidationError("Please provide at least 10 characters of description")
        return description.strip()