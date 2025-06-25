"""
Custom exception classes for the QuickCash application.

This module defines custom exceptions that provide more specific
error handling throughout the application.
"""

from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


class QuickCashException(Exception):
    """
    Base exception class for QuickCash application.
    
    All custom exceptions should inherit from this class.
    """
    default_message = "An error occurred in QuickCash application"
    default_code = "QUICKCASH_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.code}: {self.message}"
    
class QuickFundBaseException(Exception):
    """Base exception class for QuickFund application"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self):
        return {
            'error': self.message,
            'error_code': self.error_code,
            'details': self.details
        }

class PaymentProcessingError(QuickFundBaseException):
    """Exception raised when payment processing fails"""
    pass

class ValidationError(QuickCashException):
    """Exception raised for validation errors."""
    default_message = "Validation failed"
    default_code = "VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class BusinessLogicError(QuickCashException):
    """Exception raised for business logic violations."""
    default_message = "Business logic violation"
    default_code = "BUSINESS_LOGIC_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AuthenticationError(QuickCashException):
    """Exception raised for authentication failures."""
    default_message = "Authentication failed"
    default_code = "AUTHENTICATION_ERROR"
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationError(QuickCashException):
    """Exception raised for authorization failures."""
    default_message = "Access denied"
    default_code = "AUTHORIZATION_ERROR"
    status_code = status.HTTP_403_FORBIDDEN


class LoanError(QuickCashException):
    """Exception raised for loan-related errors."""
    default_message = "Loan operation failed"
    default_code = "LOAN_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class CreditScoringError(QuickCashException):
    """Exception raised for credit scoring errors."""
    default_message = "Credit scoring failed"
    default_code = "CREDIT_SCORING_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class PaymentError(QuickCashException):
    """Exception raised for payment processing errors."""
    default_message = "Payment processing failed"
    default_code = "PAYMENT_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class PaymentGatewayError(PaymentError):
    """Exception raised for payment gateway integration errors."""
    default_message = "Payment gateway error"
    default_code = "PAYMENT_GATEWAY_ERROR"
    status_code = status.HTTP_502_BAD_GATEWAY


class NotificationError(QuickCashException):
    """Exception raised for notification service errors."""
    default_message = "Notification service failed"
    default_code = "NOTIFICATION_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ExternalServiceError(QuickCashException):
    """Exception raised for external service integration errors."""
    default_message = "External service unavailable"
    default_code = "EXTERNAL_SERVICE_ERROR"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class RateLimitError(QuickCashException):
    """Exception raised when rate limits are exceeded."""
    default_message = "Rate limit exceeded"
    default_code = "RATE_LIMIT_ERROR"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class InsufficientFundsError(PaymentError):
    """Exception raised when user has insufficient funds."""
    default_message = "Insufficient funds"
    default_code = "INSUFFICIENT_FUNDS"
    status_code = status.HTTP_402_PAYMENT_REQUIRED


class LoanNotEligibleError(LoanError):
    """Exception raised when user is not eligible for loan."""
    default_message = "Not eligible for loan"
    default_code = "LOAN_NOT_ELIGIBLE"
    status_code = status.HTTP_403_FORBIDDEN


class LoanLimitExceededError(LoanError):
    """Exception raised when loan limit is exceeded."""
    default_message = "Loan limit exceeded"
    default_code = "LOAN_LIMIT_EXCEEDED"
    status_code = status.HTTP_403_FORBIDDEN


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF views.
    
    This handler provides consistent error responses for QuickCash exceptions
    and logs errors for monitoring purposes.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle QuickCash custom exceptions
    if isinstance(exc, QuickCashException):
        logger.error(
            f"QuickCash Exception: {exc.code} - {exc.message}",
            extra={
                'exception_type': type(exc).__name__,
                'exception_code': exc.code,
                'exception_message': exc.message,
                'view': context.get('view'),
                'request': context.get('request'),
            }
        )
        
        custom_response_data = {
            'error': True,
            'code': exc.code,
            'message': exc.message,
            'status_code': exc.status_code,
            'timestamp': context.get('request').META.get('HTTP_X_REQUEST_ID')
        }
        
        response = Response(custom_response_data, status=exc.status_code)
    
    # Log unexpected errors
    elif response is None:
        logger.exception(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                'exception_type': type(exc).__name__,
                'view': context.get('view'),
                'request': context.get('request'),
            }
        )
        
        # Return generic error response for unhandled exceptions
        response = Response(
            {
                'error': True,
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response