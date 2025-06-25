# /root/Quickfund/backend/quickfund_api/payments/base.py

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional

class BasePaymentProvider(ABC):
    """Abstract base class for payment providers"""
    
    @abstractmethod
    def create_payment(self, amount: Decimal, currency: str = 'NGN', **kwargs) -> Dict[str, Any]:
        """Create a payment transaction"""
        pass
    
    @abstractmethod
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a payment transaction"""
        pass
    
    @abstractmethod
    def validate_webhook(self, payload: str, signature: str) -> bool:
        """Validate webhook signature"""
        pass
    
    @abstractmethod
    def extract_reference_from_webhook(self, webhook_data: Dict[str, Any]) -> str:
        """Extract payment reference from webhook data"""
        pass
    
    @abstractmethod
    def process_refund(self, transaction_id: str, amount: Optional[Decimal] = None, reason: str = '') -> Dict[str, Any]:
        """Process a refund for a transaction"""
        pass