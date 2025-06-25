"""
Custom validators for the QuickCash application.

This module contains validation functions for various data types
used throughout the application.
"""

import re
from decimal import Decimal
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# Phone number validator
phone_number_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{1,14}$',
    message=_('Enter a valid phone number. Format: +1234567890'),
    code='invalid_phone_number'
)

# Nigerian phone number validator
nigerian_phone_validator = RegexValidator(
    regex=r'^(\+234|234|0)?[789][01]\d{8}$',
    message=_('Enter a valid Nigerian phone number'),
    code='invalid_nigerian_phone'
)

# Bank account number validator
bank_account_validator = RegexValidator(
    regex=r'^\d{10}$',
    message=_('Bank account number must be exactly 10 digits'),
    code='invalid_bank_account'
)

# BVN validator
bvn_validator = RegexValidator(
    regex=r'^\d{11}$',
    message=_('BVN must be exactly 11 digits'),
    code='invalid_bvn'
)

# NIN validator
nin_validator = RegexValidator(
    regex=r'^\d{11}$',
    message=_('NIN must be exactly 11 digits'),
    code='invalid_nin'
)


def validate_positive_decimal(value):
    """Validate that a decimal value is positive."""
    if value <= 0:
        raise ValidationError(_('This field must be a positive number.'))


def validate_loan_amount(value):
    """Validate loan amount is within acceptable range."""
    min_amount = Decimal('1000.00')
    max_amount = Decimal('5000000.00')  # 5 million naira
    
    if value < min_amount:
        raise ValidationError(
            _('Loan amount must be at least ₦%(min_amount)s') % {'min_amount': min_amount}
        )
    
    if value > max_amount:
        raise ValidationError(
            _('Loan amount cannot exceed ₦%(max_amount)s') % {'max_amount': max_amount}
        )


def validate_loan_duration(value):
    """Validate loan duration is within acceptable range."""
    min_duration = 30  # 30 days
    max_duration = 365  # 1 year
    
    if value < min_duration:
        raise ValidationError(
            _('Loan duration must be at least %(min_duration)s days') % {'min_duration': min_duration}
        )
    
    if value > max_duration:
        raise ValidationError(
            _('Loan duration cannot exceed %(max_duration)s days') % {'max_duration': max_duration}
        )


def validate_interest_rate(value):
    """Validate interest rate is within acceptable range."""
    min_rate = Decimal('0.01')  # 0.01%
    max_rate = Decimal('50.00')  # 50%
    
    if value < min_rate:
        raise ValidationError(
            _('Interest rate must be at least %(min_rate)s%%') % {'min_rate': min_rate}
        )
    
    if value > max_rate:
        raise ValidationError(
            _('Interest rate cannot exceed %(max_rate)s%%') % {'max_rate': max_rate}
        )


def validate_age(birth_date):
    """Validate that the person is at least 18 years old."""
    if not isinstance(birth_date, date):
        raise ValidationError(_('Invalid date format.'))
    
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age < 18:
        raise ValidationError(_('You must be at least 18 years old.'))
    
    if age > 100:
        raise ValidationError(_('Please enter a valid birth date.'))


def validate_future_date(value):
    """Validate that a date is in the future."""
    if value <= date.today():
        raise ValidationError(_('Date must be in the future.'))


def validate_past_date(value):
    """Validate that a date is in the past."""
    if value >= date.today():
        raise ValidationError(_('Date must be in the past.'))


def validate_file_size(value):
    """Validate uploaded file size (max 5MB)."""
    max_size = 5 * 1024 * 1024  # 5MB
    if value.size > max_size:
        raise ValidationError(_('File size cannot exceed 5MB.'))


def validate_image_file(value):
    """Validate that uploaded file is an image."""
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    extension = value.name.split('.')[-1].lower()
    
    if extension not in allowed_extensions:
        raise ValidationError(
            _('Only image files (jpg, jpeg, png, gif) are allowed.')
        )


def validate_document_file(value):
    """Validate that uploaded file is a document."""
    allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png']
    extension = value.name.split('.')[-1].lower()
    
    if extension not in allowed_extensions:
        raise ValidationError(
            _('Only document files (pdf, doc, docx, txt, jpg, jpeg, png) are allowed.')
        )


def validate_credit_score(value):
    """Validate credit score is within range."""
    if not (300 <= value <= 850):
        raise ValidationError(_('Credit score must be between 300 and 850.'))


def validate_monthly_income(value):
    """Validate monthly income is reasonable."""
    min_income = Decimal('50000.00')  # 50,000 naira
    max_income = Decimal('50000000.00')  # 50 million naira
    
    if value < min_income:
        raise ValidationError(
            _('Monthly income must be at least ₦%(min_income)s') % {'min_income': min_income}
        )
    
    if value > max_income:
        raise ValidationError(
            _('Monthly income seems unrealistic. Please verify the amount.')
        )


def validate_employment_duration(value):
    """Validate employment duration in months."""
    if value < 3:
        raise ValidationError(_('Employment duration must be at least 3 months.'))
    
    if value > 600:  # 50 years
        raise ValidationError(_('Employment duration seems unrealistic.'))


def validate_reference_name(value):
    """Validate reference name contains only letters and spaces."""
    if not re.match(r'^[a-zA-Z\s]+$', value):
        raise ValidationError(_('Name should contain only letters and spaces.'))


def validate_bank_code(value):
    """Validate Nigerian bank codes."""
    # Common Nigerian bank codes
    valid_bank_codes = [
        '044', '014', '023', '050', '070', '011', '058', '030', '057', '032',
        '033', '035', '040', '076', '082', '084', '221', '304', '329', '301'
    ]
    
    if value not in valid_bank_codes:
        raise ValidationError(_('Invalid bank code.'))


def validate_otp_code(value):
    """Validate OTP code format."""
    if not re.match(r'^\d{6}$', value):
        raise ValidationError(_('OTP must be exactly 6 digits.'))


def validate_transaction_pin(value):
    """Validate transaction PIN format."""
    if not re.match(r'^\d{4}$', value):
        raise ValidationError(_('Transaction PIN must be exactly 4 digits.'))


def validate_password_strength(password):
    """
    Validate password strength.
    
    Password must contain:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        raise ValidationError(_('Password must be at least 8 characters long.'))
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    
    if not re.search(r'[a-z]', password):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    
    if not re.search(r'\d', password):
        raise ValidationError(_('Password must contain at least one digit.'))
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        raise ValidationError(_('Password must contain at least one special character.'))


def validate_json_data(value):
    """Validate that a string is valid JSON."""
    import json
    try:
        json.loads(value)
    except (ValueError, TypeError):
        raise ValidationError(_('Invalid JSON format.'))


def validate_positive_integer(value):
    """Validate that an integer is positive."""
    if value <= 0:
        raise ValidationError(_('This field must be a positive integer.'))


def validate_percentage(value):
    """Validate that a value is a valid percentage (0-100)."""
    if not (0 <= value <= 100):
        raise ValidationError(_('Value must be between 0 and 100.'))


def validate_currency_code(value):
    """Validate currency code format."""
    if not re.match(r'^[A-Z]{3}$', value):
        raise ValidationError(_('Currency code must be 3 uppercase letters (e.g., NGN, USD).'))


def validate_webhook_url(value):
    """Validate webhook URL format."""
    if not value.startswith(('http://', 'https://')):
        raise ValidationError(_('Webhook URL must start with http:// or https://'))
    
    if len(value) > 2048:
        raise ValidationError(_('Webhook URL is too long.'))