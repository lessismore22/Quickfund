import hashlib
import hmac
import json
import requests
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from ..base import BasePaymentProvider
from ...utils.exceptions import PaymentProcessingError, ValidationError

class PaystackProvider(BasePaymentProvider):
    """Paystack payment provider implementation"""
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self.base_url = 'https://api.paystack.co'
        
        if not self.secret_key:
            print("WARNING: Paystack secret key not configured")
            # Don't raise error during import - just set a dummy key for now
            self.secret_key = 'dummy_key_for_development'
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Paystack API"""
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            else:
                raise PaymentProcessingError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            raise PaymentProcessingError(f"Paystack API request failed: {str(e)}")
    
    def create_payment(self, amount: Decimal, currency: str = 'NGN', **kwargs) -> Dict[str, Any]:
        """Create a payment transaction"""
        data = {
            'amount': int(amount * 100),  # Paystack expects amount in kobo
            'currency': currency,
            'email': kwargs.get('email'),
            'reference': kwargs.get('reference'),
            'callback_url': kwargs.get('callback_url'),
            'metadata': kwargs.get('metadata', {})
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        if not data.get('email'):
            raise ValidationError("Email is required for Paystack payments")
        
        result = self._make_request('POST', '/transaction/initialize', data)
        
        if not result.get('status'):
            raise PaymentProcessingError(f"Failed to create payment: {result.get('message')}")
        
        return {
            'transaction_id': result['data']['reference'],
            'payment_url': result['data']['authorization_url'],
            'access_code': result['data']['access_code'],
            'reference': result['data']['reference']
        }
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify a payment transaction"""
        result = self._make_request('GET', f'/transaction/verify/{reference}')
        
        if not result.get('status'):
            raise PaymentProcessingError(f"Failed to verify payment: {result.get('message')}")
        
        transaction_data = result['data']
        
        return {
            'status': transaction_data['status'],
            'reference': transaction_data['reference'],
            'amount': Decimal(transaction_data['amount']) / 100,  # Convert from kobo
            'currency': transaction_data['currency'],
            'paid_at': transaction_data.get('paid_at'),
            'channel': transaction_data.get('channel'),
            'fees': Decimal(transaction_data.get('fees', 0)) / 100,
            'customer': transaction_data.get('customer', {}),
            'metadata': transaction_data.get('metadata', {}),
            'gateway_response': transaction_data.get('gateway_response')
        }
    
    def validate_webhook(self, payload: str, signature: str) -> bool:
        """Validate webhook signature from Paystack"""
        webhook_secret = getattr(settings, 'PAYSTACK_WEBHOOK_SECRET', self.secret_key)
        
        # Create HMAC signature
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def extract_reference_from_webhook(self, webhook_data: Dict[str, Any]) -> str:
        """Extract payment reference from webhook data"""
        event = webhook_data.get('event')
        data = webhook_data.get('data', {})
        
        if event in ['charge.success', 'transfer.success', 'transfer.failed']:
            return data.get('reference', '')
        
        raise ValidationError(f"Unsupported webhook event: {event}")
    
    def process_refund(self, transaction_id: str, amount: Optional[Decimal] = None, reason: str = '') -> Dict[str, Any]:
        """Process a refund for a transaction"""
        data = {
            'transaction': transaction_id,
            'amount': int(amount * 100) if amount else None,  # Convert to kobo
            'currency': 'NGN',
            'customer_note': reason,
            'merchant_note': f'Refund processed via QuickFund: {reason}'
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self._make_request('POST', '/refund', data)
        
        if not result.get('status'):
            raise PaymentProcessingError(f"Failed to process refund: {result.get('message')}")
        
        refund_data = result['data']
        
        return {
            'refund_id': refund_data.get('id'),
            'transaction_id': refund_data.get('transaction'),
            'amount': Decimal(refund_data.get('amount', 0)) / 100,
            'currency': refund_data.get('currency'),
            'status': refund_data.get('status'),
            'created_at': refund_data.get('created_at'),
            'processed_at': refund_data.get('processed_at')
        }