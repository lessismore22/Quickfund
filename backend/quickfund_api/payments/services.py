"""
Payment processing services for QuickCash loan platform.
Handles payment gateway integrations and transaction processing.
"""

import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Repayment, PaymentTransaction
from .integrations.paystack import PaystackProvider
from .integrations.base import BasePaymentProvider, PaymentError
from quickfund_api.loans.models import Loan
from quickfund_api.users.models import CustomUser
from quickfund_api.notifications.tasks import send_payment_confirmation_task
from quickfund_api.utils.exceptions import PaymentProcessingError
from quickfund_api.utils.helpers import generate_transaction_reference
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from ..utils.exceptions import PaymentProcessingError, ValidationError      

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Central service for handling all payment operations.
    Provides unified interface for different payment providers.
    """
    
    def __init__(self):
        self.providers = {
            'paystack': PaystackProvider(),
        }
        self.default_provider = 'paystack'
    
    def get_provider(self, provider_name: str = None) -> BasePaymentProvider:
        """Get payment provider instance."""
        provider_name = provider_name or self.default_provider
        provider = self.providers.get(provider_name)
        
        if not provider:
            raise PaymentProcessingError(f"Unknown payment provider: {provider_name}")
        
        return provider
    
    def initialize_payment(
        self,
        loan: Loan,
        amount: Decimal,
        payment_type: str = 'repayment',
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction.
        
        Args:
            loan: Loan instance for payment
            amount: Payment amount
            payment_type: Type of payment (repayment, penalty, etc.)
            provider: Payment provider to use
            
        Returns:
            Dict containing payment initialization data
        """
        try:
            with transaction.atomic():
                # Validate payment amount
                self._validate_payment_amount(loan, amount, payment_type)
                
                # Generate transaction reference
                reference = generate_transaction_reference()
                
                # Create payment transaction record
                payment_transaction = PaymentTransaction.objects.create(
                    loan=loan,
                    user=loan.borrower,
                    amount=amount,
                    payment_type=payment_type,
                    reference=reference,
                    provider=provider or self.default_provider,
                    status='pending'
                )
                
                # Initialize payment with provider
                provider_instance = self.get_provider(provider)
                payment_data = provider_instance.initialize_payment(
                    amount=amount,
                    email=loan.borrower.email,
                    reference=reference,
                    callback_url=self._get_callback_url(),
                    metadata={
                        'loan_id': str(loan.id),
                        'user_id': str(loan.borrower.id),
                        'payment_type': payment_type,
                        'transaction_id': str(payment_transaction.id),
                    }
                )
                
                # Update transaction with provider data
                payment_transaction.provider_reference = payment_data.get(
                    'reference', payment_data.get('access_code')
                )
                payment_transaction.provider_data = payment_data
                payment_transaction.save()
                
                logger.info(
                    f"Payment initialized for loan {loan.id}, "
                    f"amount: {amount}, reference: {reference}"
                )
                
                return {
                    'transaction_id': payment_transaction.id,
                    'reference': reference,
                    'authorization_url': payment_data.get('authorization_url'),
                    'access_code': payment_data.get('access_code'),
                    'provider': provider or self.default_provider,
                }
                
        except Exception as e:
            logger.error(f"Failed to initialize payment: {str(e)}")
            raise PaymentProcessingError(f"Payment initialization failed: {str(e)}")
    
    def verify_payment(self, reference: str, provider: str = None) -> Dict[str, Any]:
        """
        Verify payment transaction with provider.
        
        Args:
            reference: Transaction reference
            provider: Payment provider
            
        Returns:
            Dict containing verification result
        """
        try:
            # Get transaction record
            transaction = PaymentTransaction.objects.get(reference=reference)
            
            # Verify with provider
            provider_instance = self.get_provider(provider or transaction.provider)
            verification_data = provider_instance.verify_payment(reference)
            
            # Update transaction status
            if verification_data.get('status') == 'success':
                self._process_successful_payment(transaction, verification_data)
            else:
                self._process_failed_payment(transaction, verification_data)
            
            return verification_data
            
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Payment transaction not found: {reference}")
            raise PaymentProcessingError("Transaction not found")
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            raise PaymentProcessingError(f"Verification failed: {str(e)}")
    
    def process_webhook(self, provider: str, payload: Dict[str, Any]) -> bool:
        """
        Process payment webhook from provider.
        
        Args:
            provider: Payment provider name
            payload: Webhook payload
            
        Returns:
            bool: Success status
        """
        try:
            provider_instance = self.get_provider(provider)
            
            # Validate webhook signature
            if not provider_instance.validate_webhook(payload):
                logger.warning(f"Invalid webhook signature from {provider}")
                return False
            
            # Extract transaction reference
            reference = provider_instance.extract_reference_from_webhook(payload)
            
            if not reference:
                logger.warning(f"No reference found in webhook from {provider}")
                return False
            
            # Process the payment
            self.verify_payment(reference, provider)
            
            logger.info(f"Webhook processed successfully for reference: {reference}")
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return False
    
    def create_repayment(
        self,
        loan: Loan,
        amount: Decimal,
        transaction: PaymentTransaction,
        payment_method: str = 'online'
    ) -> Repayment:
        """
        Create repayment record after successful payment.
        
        Args:
            loan: Loan instance
            amount: Repayment amount
            transaction: Payment transaction
            payment_method: Payment method used
            
        Returns:
            Repayment instance
        """
        try:
            with transaction.atomic():
                # Create repayment record
                repayment = Repayment.objects.create(
                    loan=loan,
                    amount=amount,
                    payment_date=timezone.now(),
                    payment_method=payment_method,
                    transaction_reference=transaction.reference,
                    payment_transaction=transaction,
                    status='completed'
                )
                
                # Update loan balance
                loan.outstanding_amount -= amount
                loan.total_repaid += amount
                
                # Check if loan is fully repaid
                if loan.outstanding_amount <= 0:
                    loan.status = 'paid'
                    loan.repayment_date = timezone.now()
                
                loan.save()
                
                logger.info(
                    f"Repayment created for loan {loan.id}, "
                    f"amount: {amount}, balance: {loan.outstanding_amount}"
                )
                
                return repayment
                
        except Exception as e:
            logger.error(f"Failed to create repayment: {str(e)}")
            raise PaymentProcessingError(f"Repayment creation failed: {str(e)}")
    
    def get_payment_history(
        self,
        user: CustomUser,
        loan_id: uuid.UUID = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get payment history for user or specific loan.
        
        Args:
            user: User instance
            loan_id: Optional loan ID filter
            limit: Number of records to return
            
        Returns:
            Dict containing payment history
        """
        try:
            queryset = PaymentTransaction.objects.filter(user=user)
            
            if loan_id:
                queryset = queryset.filter(loan_id=loan_id)
            
            transactions = queryset.order_by('-created_at')[:limit]
            
            # Get repayments
            repayments_qs = Repayment.objects.filter(loan__borrower=user)
            if loan_id:
                repayments_qs = repayments_qs.filter(loan_id=loan_id)
            
            repayments = repayments_qs.order_by('-payment_date')[:limit]
            
            return {
                'transactions': transactions,
                'repayments': repayments,
                'total_transactions': queryset.count(),
                'total_repayments': repayments_qs.count(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get payment history: {str(e)}")
            raise PaymentProcessingError(f"Failed to retrieve payment history: {str(e)}")
    
    def calculate_payment_schedule(self, loan: Loan) -> list:
        """
        Calculate payment schedule for a loan.
        
        Args:
            loan: Loan instance
            
        Returns:
            List of payment schedule items
        """
        schedule = []
        
        if not loan.repayment_schedule:
            return schedule
        
        repayments = Repayment.objects.filter(loan=loan).order_by('payment_date')
        repayment_amounts = {r.payment_date.date(): r.amount for r in repayments}
        
        for i, scheduled_date in enumerate(loan.repayment_schedule):
            due_amount = loan.monthly_payment_amount
            paid_amount = repayment_amounts.get(scheduled_date, Decimal('0'))
            
            schedule.append({
                'due_date': scheduled_date,
                'due_amount': due_amount,
                'paid_amount': paid_amount,
                'balance': due_amount - paid_amount,
                'status': 'paid' if paid_amount >= due_amount else 'pending',
                'is_overdue': scheduled_date < timezone.now().date() and paid_amount < due_amount,
            })
        
        return schedule
    
    def _validate_payment_amount(
        self,
        loan: Loan,
        amount: Decimal,
        payment_type: str
    ) -> None:
        """Validate payment amount against loan constraints."""
        if amount <= 0:
            raise ValidationError("Payment amount must be greater than zero")
        
        if payment_type == 'repayment':
            if amount > loan.outstanding_amount:
                raise ValidationError("Payment amount exceeds outstanding balance")
            
            # Check minimum payment amount
            min_amount = getattr(settings, 'MIN_PAYMENT_AMOUNT', Decimal('100'))
            if amount < min_amount:
                raise ValidationError(f"Minimum payment amount is {min_amount}")
    
    def _process_successful_payment(
        self,
        transaction: PaymentTransaction,
        verification_data: Dict[str, Any]
    ) -> None:
        """Process successful payment transaction."""
        try:
            with transaction.atomic():
                # Update transaction status
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.provider_response = verification_data
                transaction.save()
                
                # Create repayment record
                if transaction.payment_type == 'repayment':
                    repayment = self.create_repayment(
                        loan=transaction.loan,
                        amount=transaction.amount,
                        transaction=transaction
                    )
                    
                    # Send confirmation notification
                    send_payment_confirmation_task.delay(
                        user_id=str(transaction.user.id),
                        repayment_id=str(repayment.id)
                    )
                
                logger.info(f"Payment processed successfully: {transaction.reference}")
                
        except Exception as e:
            logger.error(f"Failed to process successful payment: {str(e)}")
            raise
    
    def _process_failed_payment(
        self,
        transaction: PaymentTransaction,
        verification_data: Dict[str, Any]
    ) -> None:
        """Process failed payment transaction."""
        transaction.status = 'failed'
        transaction.failure_reason = verification_data.get('message', 'Payment failed')
        transaction.provider_response = verification_data
        transaction.save()
        
        logger.warning(f"Payment failed: {transaction.reference}")
    
    def _get_callback_url(self) -> str:
        """Get payment callback URL."""
        base_url = getattr(settings, 'BASE_URL', 'https://api.quickcash.com')
        return f"{base_url}/api/payments/callback/"


class RefundService:
    """Service for handling payment refunds."""
    
    def __init__(self):
        self.payment_service = PaymentService()
    
    def process_refund(
        self,
        transaction: PaymentTransaction,
        amount: Decimal = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Process refund for a payment transaction.
        
        Args:
            transaction: Original payment transaction
            amount: Refund amount (full amount if not specified)
            reason: Refund reason
            
        Returns:
            Dict containing refund details
        """
        try:
            refund_amount = amount or transaction.amount
            
            # Validate refund
            self._validate_refund(transaction, refund_amount)
            
            # Process refund with provider
            provider = self.payment_service.get_provider(transaction.provider)
            refund_data = provider.process_refund(
                transaction.provider_reference,
                refund_amount,
                reason
            )
            
            # Create refund record
            refund_transaction = PaymentTransaction.objects.create(
                loan=transaction.loan,
                user=transaction.user,
                amount=-refund_amount,  # Negative amount for refund
                payment_type='refund',
                reference=generate_transaction_reference(),
                provider=transaction.provider,
                status='completed',
                parent_transaction=transaction,
                provider_response=refund_data
            )
            
            logger.info(
                f"Refund processed: {refund_amount} for transaction {transaction.reference}"
            )
            
            return {
                'refund_id': refund_transaction.id,
                'refund_reference': refund_transaction.reference,
                'amount': refund_amount,
                'status': 'completed',
                'provider_data': refund_data
            }
            
        except Exception as e:
            logger.error(f"Refund processing failed: {str(e)}")
            raise PaymentProcessingError(f"Refund failed: {str(e)}")
    
    def _validate_refund(
        self,
        transaction: PaymentTransaction,
        amount: Decimal
    ) -> None:
        """Validate refund request."""
        if transaction.status != 'completed':
            raise ValidationError("Can only refund completed transactions")
        
        if amount <= 0 or amount > transaction.amount:
            raise ValidationError("Invalid refund amount")
        
        # Check if already refunded
        existing_refunds = PaymentTransaction.objects.filter(
            parent_transaction=transaction,
            payment_type='refund'
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        
        if abs(existing_refunds) + amount > transaction.amount:
            raise ValidationError("Refund amount exceeds available balance")
        


class PaymentService:
    def __init__(self):
        # Don't instantiate providers here - use lazy loading
        self._providers = {}
    
    def _get_provider(self, provider_name: str):
        """Lazy load payment providers"""
        if provider_name not in self._providers:
            if provider_name == 'paystack':
                from .providers.paystack import PaystackProvider
                self._providers['paystack'] = PaystackProvider()
            elif provider_name == 'flutterwave':
                # from .providers.flutterwave import FlutterwaveProvider
                # self._providers['flutterwave'] = FlutterwaveProvider()
                raise NotImplementedError("Flutterwave provider not implemented yet")
            else:
                raise ValueError(f"Unknown payment provider: {provider_name}")
        
        return self._providers[provider_name]
    
    def create_payment(self, provider_name: str, amount: Decimal, **kwargs) -> Dict[str, Any]:
        """Create a payment using the specified provider"""
        provider = self._get_provider(provider_name)
        return provider.create_payment(amount, **kwargs)
    
    def verify_payment(self, provider_name: str, reference: str) -> Dict[str, Any]:
        """Verify a payment using the specified provider"""
        provider = self._get_provider(provider_name)
        return provider.verify_payment(reference)
    
    def validate_webhook(self, provider_name: str, payload: str, signature: str) -> bool:
        """Validate webhook signature"""
        provider = self._get_provider(provider_name)
        return provider.validate_webhook(payload, signature)
    
    def extract_reference_from_webhook(self, provider_name: str, webhook_data: Dict[str, Any]) -> str:
        """Extract payment reference from webhook"""
        provider = self._get_provider(provider_name)
        return provider.extract_reference_from_webhook(webhook_data)
    
    def process_refund(self, provider_name: str, transaction_id: str, amount: Optional[Decimal] = None, reason: str = '') -> Dict[str, Any]:
        """Process a refund"""
        provider = self._get_provider(provider_name)
        return provider.process_refund(transaction_id, amount, reason)

class PaymentProcessorService:
    """Service for handling payment processing logic"""
    
    def __init__(self):
        self.payment_service = PaymentService()
    
    def initialize_payment(self, amount: Decimal, email: str, provider: str = 'paystack', **kwargs) -> Dict[str, Any]:
        """Initialize a payment transaction"""
        try:
            payment_data = {
                'email': email,
                'reference': kwargs.get('reference'),
                'callback_url': kwargs.get('callback_url'),
                'metadata': kwargs.get('metadata', {})
            }
            
            result = self.payment_service.create_payment(provider, amount, **payment_data)
            return {
                'status': 'success',
                'data': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def verify_payment_transaction(self, reference: str, provider: str = 'paystack') -> Dict[str, Any]:
        """Verify a payment transaction"""
        try:
            result = self.payment_service.verify_payment(provider, reference)
            return {
                'status': 'success',
                'data': result
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def handle_webhook(self, provider: str, payload: str, signature: str) -> Dict[str, Any]:
        """Handle payment webhook"""
        try:
            # Validate webhook
            if not self.payment_service.validate_webhook(provider, payload, signature):
                return {
                    'status': 'error',
                    'message': 'Invalid webhook signature'
                }
            
            # Parse webhook data
            import json
            webhook_data = json.loads(payload)
            
            # Extract reference
            reference = self.payment_service.extract_reference_from_webhook(provider, webhook_data)
            
            # Verify payment
            payment_result = self.verify_payment_transaction(reference, provider)
            
            return {
                'status': 'success',
                'reference': reference,
                'payment_data': payment_result
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

# Create a function to get service instances instead of module-level instantiation
def get_payment_service() -> PaymentService:
    """Get PaymentService instance"""
    return PaymentService()

def get_payment_processor_service() -> PaymentProcessorService:
    """Get PaymentProcessorService instance"""
    return PaymentProcessorService()

# If you need backward compatibility, you can uncomment this AFTER Django is fully loaded
# But it's better to use the functions above in your views
# payment_service = PaymentService()
# payment_processor_service = PaymentProcessorService()


# Service instances
payment_service = PaymentService()
refund_service = RefundService()