"""
Base payment provider interface for QuickCash.
Defines the common interface that all payment providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Base exception for payment processing errors."""
    
    def __init__(self, message: str, code: str = None, provider_response: Dict = None):
        super().__init__(message)
        self.code = code
        self.provider_response = provider_response or {}


class PaymentValidationError(PaymentError):
    """Exception for payment validation errors."""
    pass


class PaymentProviderError(PaymentError):
    """Exception for payment provider specific errors."""
    pass


class PaymentNetworkError(PaymentError):
    """Exception for network-related payment errors."""
    pass


@dataclass
class PaymentInitialization:
    """Data class for payment initialization response."""
    authorization_url: str
    access_code: str
    reference: str
    provider_reference: str
    status: str
    amount: Decimal
    currency: str = 'NGN'
    metadata: Dict[str, Any] = None


@dataclass
class PaymentVerification:
    """Data class for payment verification response."""
    status: str
    reference: str
    amount: Decimal
    currency: str
    gateway_response: str
    paid_at: str = None
    channel: str = None
    fees: Decimal = None
    authorization: Dict[str, Any] = None
    customer: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class RefundResult:
    """Data class for refund operation response."""
    status: str
    refund_reference: str
    amount: Decimal
    currency: str
    transaction_reference: str
    refunded_at: str = None
    reason: str = None


class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    All payment providers must inherit from this class and implement the required methods.
    """
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.logger = logging.getLogger(f'payments.{provider_name}')
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the payment provider API."""
        pass
    
    @property
    @abstractmethod
    def public_key(self) -> str:
        """Public key for the payment provider."""
        pass
    
    @property
    @abstractmethod
    def secret_key(self) -> str:
        """Secret key for the payment provider."""
        pass
    
    @abstractmethod
    def initialize_payment(
        self,
        amount: Decimal,
        email: str,
        reference: str,
        callback_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction.
        
        Args:
            amount: Payment amount
            email: Customer email
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional metadata for the transaction
            
        Returns:
            Dict containing payment initialization data
            
        Raises:
            PaymentError: If initialization fails
        """
        pass
    
    @abstractmethod
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify a payment transaction.
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            Dict containing verification result
            
        Raises:
            PaymentError: If verification fails
        """
        pass
    
    @abstractmethod
    def process_refund(
        self,
        transaction_reference: str,
        amount: Decimal,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Process a refund for a transaction.
        
        Args:
            transaction_reference: Original transaction reference
            amount: Refund amount
            reason: Refund reason
            
        Returns:
            Dict containing refund result
            
        Raises:
            PaymentError: If refund fails
        """
        pass
    
    @abstractmethod
    def validate_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Validate webhook signature and payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            bool: True if webhook is valid
        """
        pass
    
    @abstractmethod
    def extract_reference_from_webhook(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract transaction reference from webhook payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            str: Transaction reference or None if not found
        """
        pass
    
    def get_supported_currencies(self) -> list:
        """
        Get list of supported currencies.
        
        Returns:
            List of supported currency codes
        """
        return ['NGN']  # Default to Nigerian Naira
    
    def get_supported_channels(self) -> list:
        """
        Get list of supported payment channels.
        
        Returns:
            List of supported payment channels
        """
        return ['card', 'bank', 'ussd', 'mobile_money']
    
    def format_amount(self, amount: Decimal) -> int:
        """
        Format amount for provider API (usually in kobo/cents).
        
        Args:
            amount: Amount in Naira/main currency unit
            
        Returns:
            int: Amount in kobo/cents
        """
        return int(amount * 100)
    
    def parse_amount(self, amount: int) -> Decimal:
        """
        Parse amount from provider API (from kobo/cents to main unit).
        
        Args:
            amount: Amount in kobo/cents
            
        Returns:
            Decimal: Amount in Naira/main currency unit
        """
        return Decimal(str(amount)) / 100
    
    def build_authorization_headers(self) -> Dict[str, str]:
        """
        Build authorization headers for API requests.
        
        Returns:
            Dict containing authorization headers
        """
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def handle_api_error(self, response_data: Dict[str, Any], status_code: int) -> None:
        """
        Handle API error responses.
        
        Args:
            response_data: API response data
            status_code: HTTP status code
            
        Raises:
            PaymentError: Appropriate payment error based on response
        """
        message = response_data.get('message', 'Unknown error occurred')
        
        if status_code == 400:
            raise PaymentValidationError(
                message,
                code='validation_error',
                provider_response=response_data
            )
        elif status_code == 401:
            raise PaymentProviderError(
                'Authentication failed',
                code='auth_error',
                provider_response=response_data
            )
        elif status_code >= 500:
            raise PaymentNetworkError(
                'Provider service unavailable',
                code='service_error',
                provider_response=response_data
            )
        else:
            raise PaymentError(
                message,
                code='unknown_error',
                provider_response=response_data
            )
    
    def log_request(self, method: str, url: str, data: Dict = None) -> None:
        """Log API request for debugging."""
        self.logger.info(f"{method} {url}")
        if data and self.logger.isEnabledFor(logging.DEBUG):
            # Don't log sensitive data in production
            safe_data = {k: v for k, v in data.items() if k not in ['key', 'secret']}
            self.logger.debug(f"Request data: {safe_data}")
    
    def log_response(self, status_code: int, response_data: Dict = None) -> None:
        """Log API response for debugging."""
        self.logger.info(f"Response status: {status_code}")
        if response_data and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Response data: {response_data}")
    
    def validate_amount(self, amount: Decimal) -> None:
        """
        Validate payment amount.
        
        Args:
            amount: Amount to validate
            
        Raises:
            PaymentValidationError: If amount is invalid
        """
        if amount <= 0:
            raise PaymentValidationError("Amount must be greater than zero")
        
        # Check minimum amount (1 Naira)
        if amount < Decimal('1.00'):
            raise PaymentValidationError("Amount must be at least ₦1.00")
        
        # Check maximum amount (1 million Naira)
        if amount > Decimal('1000000.00'):
            raise PaymentValidationError("Amount cannot exceed ₦1,000,000.00")
    
    def validate_email(self, email: str) -> None:
        """
        Validate email address.
        
        Args:
            email: Email to validate
            
        Raises:
            PaymentValidationError: If email is invalid
        """
        import re
        
        if not email:
            raise PaymentValidationError("Email is required")
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise PaymentValidationError("Invalid email format")
    
    def validate_reference(self, reference: str) -> None:
        """
        Validate transaction reference.
        
        Args:
            reference: Reference to validate
            
        Raises:
            PaymentValidationError: If reference is invalid
        """
        if not reference:
            raise PaymentValidationError("Reference is required")
        
        if len(reference) < 8:
            raise PaymentValidationError("Reference must be at least 8 characters")
        
        if len(reference) > 100:
            raise PaymentValidationError("Reference cannot exceed 100 characters")
        
        # Check for valid characters (alphanumeric, dash, underscore)
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', reference):
            raise PaymentValidationError("Reference contains invalid characters")


class MockPaymentProvider(BasePaymentProvider):
    """Mock payment provider for testing purposes."""
    
    def __init__(self):
        super().__init__('mock')
    
    @property
    def base_url(self) -> str:
        return 'https://mock-payment-provider.com'
    
    @property
    def public_key(self) -> str:
        return 'pk_test_mock'
    
    @property
    def secret_key(self) -> str:
        return 'sk_test_mock'
    
    def initialize_payment(
        self,
        amount: Decimal,
        email: str,
        reference: str,
        callback_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Mock payment initialization."""
        self.validate_amount(amount)
        self.validate_email(email)
        self.validate_reference(reference)
        
        return {
            'status': True,
            'message': 'Payment initialized',
            'data': {
                'authorization_url': f'https://mock-payment.com/pay/{reference}',
                'access_code': f'mock_access_{reference}',
                'reference': reference,
            }
        }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Mock payment verification."""
        self.validate_reference(reference)
        
        return {
            'status': 'success',
            'reference': reference,
            'amount': 10000,  # ₦100.00 in kobo
            'currency': 'NGN',
            'gateway_response': 'Successful',
            'paid_at': '2023-01-01T12:00:00.000Z',
            'channel': 'card'
        }
    
    def process_refund(
        self,
        transaction_reference: str,
        amount: Decimal,
        reason: str = None
    ) -> Dict[str, Any]:
        """Mock refund processing."""
        return {
            'status': 'success',
            'refund_reference': f'refund_{transaction_reference}',
            'amount': self.format_amount(amount),
            'currency': 'NGN',
            'transaction_reference': transaction_reference,
            'reason': reason or 'Refund requested'
        }
    
    def validate_webhook(self, payload: Dict[str, Any]) -> bool:
        """Mock webhook validation."""
        return True
    
    def extract_reference_from_webhook(self, payload: Dict[str, Any]) -> Optional[str]:
        """Mock reference extraction."""
        return payload.get('data', {}).get('reference')