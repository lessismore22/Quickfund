import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_bvn(value):
    """
    Validate Bank Verification Number (BVN)
    BVN should be exactly 11 digits
    """
    if not value:
        raise ValidationError(_('BVN is required.'))
    
    # Remove any whitespace
    bvn = str(value).strip()
    
    # Check if BVN contains only digits
    if not bvn.isdigit():
        raise ValidationError(_('BVN must contain only digits.'))
    
    # Check if BVN is exactly 11 digits
    if len(bvn) != 11:
        raise ValidationError(_('BVN must be exactly 11 digits.'))
    
    return bvn


def validate_phone_number(value):
    """
    Validate Nigerian phone number
    Accepts formats: +234XXXXXXXXXX, 234XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX
    """
    if not value:
        raise ValidationError(_('Phone number is required.'))
    
    # Remove all whitespace and special characters except +
    phone = re.sub(r'[^\d+]', '', str(value))
    
    # Nigerian phone number patterns
    patterns = [
        r'^\+234[789]\d{9}$',  # +234XXXXXXXXXX
        r'^234[789]\d{9}$',    # 234XXXXXXXXXX
        r'^0[789]\d{9}$',      # 0XXXXXXXXXX
        r'^[789]\d{9}$'        # XXXXXXXXXX
    ]
    
    if not any(re.match(pattern, phone) for pattern in patterns):
        raise ValidationError(_(
            'Enter a valid Nigerian phone number. '
            'Accepted formats: +234XXXXXXXXXX, 0XXXXXXXXXX, or XXXXXXXXXX'
        ))
    
    return phone


def validate_age(date_of_birth):
    """
    Validate that user is at least 18 years old
    """
    from django.utils import timezone
    from datetime import date
    
    if not date_of_birth:
        raise ValidationError(_('Date of birth is required.'))
    
    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
    
    if age < 18:
        raise ValidationError(_('You must be at least 18 years old to register.'))
    
    if age > 100:
        raise ValidationError(_('Please enter a valid date of birth.'))
    
    return date_of_birth


def validate_name(value):
    """
    Validate that name contains only letters, spaces, hyphens, and apostrophes
    """
    if not value:
        raise ValidationError(_('This field is required.'))
    
    # Remove extra whitespace
    name = value.strip()
    
    if len(name) < 2:
        raise ValidationError(_('Name must be at least 2 characters long.'))
    
    if len(name) > 50:
        raise ValidationError(_('Name must not exceed 50 characters.'))
    
    # Allow letters, spaces, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValidationError(_(
            'Name can only contain letters, spaces, hyphens, and apostrophes.'
        ))
    
    return name


def validate_credit_score(value):
    """
    Validate credit score range
    """
    if value is not None:
        if value < 300 or value > 850:
            raise ValidationError(_(
                'Credit score must be between 300 and 850.'
            ))
    
    return value


def validate_address(value):
    """
    Validate address format
    """
    if not value:
        raise ValidationError(_('Address is required.'))
    
    address = value.strip()
    
    if len(address) < 10:
        raise ValidationError(_('Address must be at least 10 characters long.'))
    
    if len(address) > 200:
        raise ValidationError(_('Address must not exceed 200 characters.'))
    
    return address