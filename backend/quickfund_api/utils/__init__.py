"""
Utility functions and helpers for the QuickCash application.

This package contains various utility modules including:
- exceptions: Custom exception classes
- validators: Data validation functions
- decorators: Custom decorators for views and functions
- mixins: Reusable class mixins
- helpers: General helper functions
- constants: Application constants
"""

__version__ = '1.0.0'
__author__ = 'QuickCash Development Team'

# Import commonly used utilities for easy access
from .exceptions import (
    QuickCashException,
    ValidationError,
    BusinessLogicError,
    PaymentError,
    CreditScoringError,
)

from .constants import (
    LOAN_STATUS_CHOICES,
    REPAYMENT_STATUS_CHOICES,
    NOTIFICATION_TYPES,
    USER_TYPES,
)

from .helpers import (
    generate_reference_number,
    format_currency,
    send_notification,
)

__all__ = [
    'QuickCashException',
    'ValidationError',
    'BusinessLogicError',
    'PaymentError',
    'CreditScoringError',
    'LOAN_STATUS_CHOICES',
    'REPAYMENT_STATUS_CHOICES',
    'NOTIFICATION_TYPES',
    'USER_TYPES',
    'generate_reference_number',
    'format_currency',
    'send_notification',
]