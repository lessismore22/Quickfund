"""
Paystack payment provider integration for QuickCash.
Handles all Paystack API interactions for payment processing.
"""

import json
import hashlib
import hmac
import requests
from decimal import Decimal
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from django.conf import settings

from .base import BasePaymentProvider, PaymentError, PaymentValidationError, PaymentNetworkError


class PaystackProvider(BasePaymentProvider):
    """Paystack payment provider implementation."""
    
    def __init__(self):
        super().__init__('paystack')
        self._base_url = 'https://api.paystack.co/'
        self._public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self._secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        
        if not self._secret_key:
            self.logger.warning("Paystack secret key not configured")
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    @property
    def public_key(self) -> str:
        return self._public_key
    
    @property
    def secret_key(self) -> str:
        return self._secret_key
    
    def initialize_payment(
        self,
        amount: Decimal,
        email: str,
        reference: str,
        callback_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initialize payment with Paystack.
        
        Args:
            amount: Payment amount in Naira
            email: Customer email
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional transaction metadata
        """