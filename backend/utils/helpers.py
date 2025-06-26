"""
Utility helper functions for the QuickCash application.
"""

import logging
import random
import re
import uuid
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Union, List
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import phonenumbers
from phonenumbers import NumberParseException


User = get_user_model()


def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a unique identifier with optional prefix.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part
    
    Returns:
        Unique identifier string
    """
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    return f"{prefix}{random_part}" if prefix else random_part

def generate_reference_number():
    """Generate a unique reference number for transactions"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"QF{timestamp}{random_chars}"

def generate_loan_reference() -> str:
    """Generate a unique loan reference number."""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_part = generate_unique_id(length=6)
    return f"QC{timestamp}{unique_part}"


def generate_transaction_reference() -> str:
    """Generate a unique transaction reference."""
    return f"TXN{generate_unique_id(length=12)}"


def validate_phone_number(phone_number: str, country_code: str = "NG") -> Dict[str, Any]:
    """
    Validate and format phone number.
    
    Args:
        phone_number: Phone number to validate
        country_code: Country code (default: NG for Nigeria)
    
    Returns:
        Dictionary with validation result and formatted number
    """
    try:
        parsed_number = phonenumbers.parse(phone_number, country_code)
        is_valid = phonenumbers.is_valid_number(parsed_number)
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        
        return {
            'is_valid': is_valid,
            'formatted_number': formatted_number,
            'country_code': parsed_number.country_code,
            'national_number': parsed_number.national_number
        }
    except NumberParseException:
        return {
            'is_valid': False,
            'formatted_number': None,
            'error': 'Invalid phone number format'
        }


def validate_bvn(bvn: str) -> bool:
    """
    Validate Bank Verification Number (BVN).
    
    Args:
        bvn: BVN to validate
    
    Returns:
        Boolean indicating if BVN is valid
    """
    if not bvn or len(bvn) != 11:
        return False
    
    return bvn.isdigit()


def validate_nin(nin: str) -> bool:
    """
    Validate National Identification Number (NIN).
    
    Args:
        nin: NIN to validate
    
    Returns:
        Boolean indicating if NIN is valid
    """
    if not nin or len(nin) != 11:
        return False
    
    return nin.isdigit()

logger = logging.getLogger(__name__)

def send_notification(user, subject, message, notification_type='email'):
    """
    Send notification to user via email or other methods
    """
    try:
        if notification_type == 'email' and user.email:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Email notification sent to {user.email}")
            return True
        else:
            logger.warning(f"Notification type {notification_type} not supported or user has no email")
            return False
    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")
        return False

def calculate_loan_interest(principal: Decimal, rate: Decimal, duration_days: int) -> Decimal:
    """
    Calculate simple interest for a loan.
    
    Args:
        principal: Loan principal amount
        rate: Interest rate (as decimal, e.g., 0.15 for 15%)
        duration_days: Loan duration in days
    
    Returns:
        Interest amount
    """
    # Convert days to years for calculation
    years = Decimal(duration_days) / Decimal(365)
    interest = principal * rate * years
    return interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_total_repayment(principal: Decimal, interest: Decimal) -> Decimal:
    """
    Calculate total repayment amount.
    
    Args:
        principal: Loan principal
        interest: Interest amount
    
    Returns:
        Total repayment amount
    """
    total = principal + interest
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_daily_penalty(overdue_amount: Decimal, penalty_rate: Decimal) -> Decimal:
    """
    Calculate daily penalty for overdue loans.
    
    Args:
        overdue_amount: Amount that is overdue
        penalty_rate: Daily penalty rate (as decimal)
    
    Returns:
        Daily penalty amount
    """
    penalty = overdue_amount * penalty_rate
    return penalty.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def is_business_day(date: datetime) -> bool:
    """
    Check if a given date is a business day (Monday-Friday).
    
    Args:
        date: Date to check
    
    Returns:
        Boolean indicating if it's a business day
    """
    return date.weekday() < 5  # Monday is 0, Sunday is 6


def get_next_business_day(date: datetime) -> datetime:
    """
    Get the next business day from a given date.
    
    Args:
        date: Starting date
    
    Returns:
        Next business day
    """
    next_day = date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day


def hash_sensitive_data(data: str) -> str:
    """
    Hash sensitive data using SHA-256.
    
    Args:
        data: Data to hash
    
    Returns:
        Hashed data
    """
    return hashlib.sha256(data.encode()).hexdigest()


def mask_phone_number(phone_number: str) -> str:
    """
    Mask phone number for display purposes.
    
    Args:
        phone_number: Phone number to mask
    
    Returns:
        Masked phone number
    """
    if len(phone_number) < 8:
        return phone_number
    
    return phone_number[:3] + '*' * (len(phone_number) - 6) + phone_number[-3:]


def mask_email(email: str) -> str:
    """
    Mask email address for display purposes.
    
    Args:
        email: Email to mask
    
    Returns:
        Masked email
    """
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return email
    
    masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def format_currency(amount: Union[int, float, Decimal], currency: str = "NGN") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Amount to format
        currency: Currency code
    
    Returns:
        Formatted currency string
    """
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    
    amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    if currency == "NGN":
        return f"₦{amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


def parse_duration_string(duration_str: str) -> int:
    """
    Parse duration string to days.
    
    Args:
        duration_str: Duration string (e.g., "30d", "2w", "1m")
    
    Returns:
        Duration in days
    """
    if not duration_str:
        return 0
    
    duration_str = duration_str.lower().strip()
    
    # Extract number and unit
    match = re.match(r'^(\d+)([dwmy])$', duration_str)
    if not match:
        return 0
    
    number, unit = match.groups()
    number = int(number)
    
    if unit == 'd':  # days
        return number
    elif unit == 'w':  # weeks
        return number * 7
    elif unit == 'm':  # months (approximate)
        return number * 30
    elif unit == 'y':  # years (approximate)
        return number * 365
    
    return 0


def get_age_from_date(birth_date: datetime) -> int:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Date of birth
    
    Returns:
        Age in years
    """
    today = timezone.now().date()
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP (One-Time Password).
    
    Args:
        length: Length of the OTP
    
    Returns:
        OTP string
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        Boolean indicating if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def clean_text(text: str) -> str:
    """
    Clean and normalize text input.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text


def calculate_credit_utilization(total_credit: Decimal, used_credit: Decimal) -> Decimal:
    """
    Calculate credit utilization ratio.
    
    Args:
        total_credit: Total available credit
        used_credit: Currently used credit
    
    Returns:
        Credit utilization ratio as decimal
    """
    if total_credit <= 0:
        return Decimal('0')
    
    utilization = used_credit / total_credit
    return utilization.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def is_weekend(date: datetime) -> bool:
    """
    Check if a date falls on a weekend.
    
    Args:
        date: Date to check
    
    Returns:
        Boolean indicating if it's a weekend
    """
    return date.weekday() >= 5  # Saturday is 5, Sunday is 6


def get_financial_year_start(date: datetime) -> datetime:
    """
    Get the start of the financial year for a given date.
    Assumes financial year starts in January.
    
    Args:
        date: Reference date
    
    Returns:
        Start of financial year
    """
    return datetime(date.year, 1, 1, tzinfo=date.tzinfo)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 50:
        name = name[:50]
    
    return f"{name}.{ext}" if ext else name


def create_audit_log_entry(user: Any, action: str, model_name: str, object_id: str, changes: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create an audit log entry.
    
    Args:
        user: User performing the action
        action: Action performed (CREATE, UPDATE, DELETE)
        model_name: Name of the model affected
        object_id: ID of the object affected
        changes: Dictionary of changes made
    
    Returns:
        Audit log entry dictionary
    """
    return {
        'user_id': user.id if user else None,
        'username': user.username if user else 'system',
        'action': action,
        'model_name': model_name,
        'object_id': str(object_id),
        'changes': changes or {},
        'timestamp': timezone.now().isoformat(),
        'ip_address': getattr(user, 'current_ip', None) if user else None
    }


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
    
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
    
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_divide(numerator: Union[int, float, Decimal], denominator: Union[int, float, Decimal], default: Union[int, float, Decimal] = 0) -> Union[int, float, Decimal]:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Default value to return if denominator is zero
    
    Returns:
        Division result or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

