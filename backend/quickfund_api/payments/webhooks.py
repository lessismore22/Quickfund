"""
Payment gateway webhook handlers for QuickCash.
Handles incoming webhook notifications from payment providers.
"""

import json
import logging
import hashlib
import hmac
from typing import Dict, Any

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction

from .services import payment_service
from .models import PaymentTransaction, WebhookLog
from utils.decorators import log_webhook_request
from utils.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)


class BaseWebhookHandler:
    """Base class for webhook handlers."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        raise NotImplementedError("Subclasses must implement validate_signature")
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook payload."""
        raise NotImplementedError("Subclasses must implement process_webhook")
    
    def log_webhook(self, payload: Dict[str, Any], status: str, response: str = None):
        """Log webhook request for debugging and audit."""
        try:
            WebhookLog.objects.create(
                provider=self.provider_name,
                event_type=payload.get('event', 'unknown'),
                payload=payload,
                status=status,
                response_data=response,
                reference=self._extract_reference(payload)
            )
        except Exception as e:
            logger.error(f"Failed to log webhook: {str(e)}")
    
    def _extract_reference(self, payload: Dict[str, Any]) -> str:
        """Extract transaction reference from payload."""
        return payload.get('data', {}).get('reference', '')


class PaystackWebhookHandler(BaseWebhookHandler):
    """Paystack webhook handler."""
    
    def __init__(self):
        super().__init__('paystack')
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate Paystack webhook signature."""
        try:
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Paystack signature validation failed: {str(e)}")
            return False
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Paystack webhook payload."""
        event = payload.get('event')
        data = payload.get('data', {})
        
        if event == 'charge.success':
            return self._handle_successful_payment(data)
        elif event == 'charge.failed':
            return self._handle_failed_payment(data)
        elif event == 'transfer.success':
            return self._handle_successful_transfer(data)
        elif event == 'transfer.failed':
            return self._handle_failed_transfer(data)
        else:
            logger.info(f"Unhandled Paystack event: {event}")
            return {'status': 'ignored', 'message': f'Event {event} not handled'}
    
    def _handle_successful_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        try:
            reference = data.get('reference')
            if not reference:
                raise WebhookValidationError("No reference found in webhook data")
            
            # Process the payment
            result = payment_service.verify_payment(reference, 'paystack')
            
            logger.info(f"Paystack payment success processed: {reference}")
            
            return {
                'status': 'success',
                'message': 'Payment processed successfully',
                'reference': reference
            }
            
        except Exception as e:
            logger.error(f"Failed to process Paystack success webhook: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _handle_failed_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        try:
            reference = data.get('reference')
            if not reference:
                raise WebhookValidationError("No reference found in webhook data")
            
            # Update transaction status
            try:
                transaction = PaymentTransaction.objects.get(reference=reference)
                transaction.status = 'failed'
                transaction.failure_reason = data.get('gateway_response', 'Payment failed')
                transaction.provider_response = data
                transaction.save()
                
                logger.info(f"Paystack payment failure processed: {reference}")
                
            except PaymentTransaction.DoesNotExist:
                logger.warning(f"Transaction not found for failed payment: {reference}")
            
            return {
                'status': 'success',
                'message': 'Failed payment processed',
                'reference': reference
            }
            
        except Exception as e:
            logger.error(f"Failed to process Paystack failure webhook: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _handle_successful_transfer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful transfer webhook (for refunds)."""
        try:
            reference = data.get('reference')
            logger.info(f"Paystack transfer success: {reference}")
            
            return {
                'status': 'success',
                'message': 'Transfer processed successfully',
                'reference': reference
            }
            
        except Exception as e:
            logger.error(f"Failed to process Paystack transfer webhook: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _handle_failed_transfer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed transfer webhook."""
        try:
            reference = data.get('reference')
            logger.warning(f"Paystack transfer failed: {reference}")
            
            return {
                'status': 'success',
                'message': 'Failed transfer processed',
                'reference': reference
            }
            
        except Exception as e:
            logger.error(f"Failed to process Paystack transfer failure webhook: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_http_methods(["POST"]), name='dispatch')
@method_decorator(log_webhook_request, name='dispatch')
class PaystackWebhookView(View):
    """Paystack webhook endpoint."""
    
    def __init__(self):
        super().__init__()
        self.handler = PaystackWebhookHandler()
    
    def post(self, request):
        """Handle incoming Paystack webhook."""
        try:
            # Get signature from headers
            signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
            if not signature:
                logger.warning("Missing Paystack signature")
                return HttpResponseBadRequest("Missing signature")
            
            # Validate signature
            payload_body = request.body
            if not self.handler.validate_signature(payload_body, signature):
                logger.warning("Invalid Paystack signature")
                return HttpResponseBadRequest("Invalid signature")
            
            # Parse payload
            try:
                payload = json.loads(payload_body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload: {str(e)}")
                return HttpResponseBadRequest("Invalid JSON")
            
            # Process webhook
            with transaction.atomic():
                result = self.handler.process_webhook(payload)
                
                # Log webhook
                self.handler.log_webhook(
                    payload=payload,
                    status=result.get('status', 'unknown'),
                    response=json.dumps(result)
                )
                
                if result.get('status') == 'error':
                    logger.error(f"Webhook processing error: {result.get('message')}")
                    return HttpResponseBadRequest(result.get('message', 'Processing failed'))
            
            return HttpResponse("OK")
            
        except Exception as e:
            logger.error(f"Paystack webhook processing failed: {str(e)}")
            return HttpResponseBadRequest("Processing failed")


class WebhookProcessor:
    """Central webhook processor for all providers."""
    
    def __init__(self):
        self.handlers = {
            'paystack': PaystackWebhookHandler(),
        }
    
    def process_webhook(self, provider: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook for specified provider."""
        handler = self.handlers.get(provider)
        if not handler:
            raise WebhookValidationError(f"Unknown provider: {provider}")
        
        return handler.process_webhook(payload)
    
    def validate_webhook(self, provider: str, payload: bytes, signature: str) -> bool:
        """Validate webhook signature for specified provider."""
        handler = self.handlers.get(provider)
        if not handler:
            return False
        
        return handler.validate_signature(payload, signature)


# Global webhook processor instance
webhook_processor = WebhookProcessor()


@csrf_exempt
@require_http_methods(["POST"])
@log_webhook_request
def generic_webhook_handler(request, provider):
    """Generic webhook handler for any provider."""
    try:
        # Validate provider
        if provider not in webhook_processor.handlers:
            logger.warning(f"Unknown webhook provider: {provider}")
            return HttpResponseBadRequest("Unknown provider")
        
        # Get signature based on provider
        signature_header_map = {
            'paystack': 'HTTP_X_PAYSTACK_SIGNATURE',
        }
        
        signature_header = signature_header_map.get(provider)
        if not signature_header:
            logger.warning(f"No signature header configured for provider: {provider}")
            return HttpResponseBadRequest("No signature validation configured")
        
        signature = request.META.get(signature_header, '')
        if not signature:
            logger.warning(f"Missing signature for provider: {provider}")
            return HttpResponseBadRequest("Missing signature")
        
        # Validate signature
        payload_body = request.body
        if not webhook_processor.validate_webhook(provider, payload_body, signature):
            logger.warning(f"Invalid signature for provider: {provider}")
            return HttpResponseBadRequest("Invalid signature")
        
        # Parse and process payload
        try:
            payload = json.loads(payload_body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload from {provider}: {str(e)}")
            return HttpResponseBadRequest("Invalid JSON")
        
        # Process webhook
        with transaction.atomic():
            result = webhook_processor.process_webhook(provider, payload)
            
            # Log webhook
            handler = webhook_processor.handlers[provider]
            handler.log_webhook(
                payload=payload,
                status=result.get('status', 'unknown'),
                response=json.dumps(result)
            )
            
            if result.get('status') == 'error':
                logger.error(f"Webhook processing error for {provider}: {result.get('message')}")
                return HttpResponseBadRequest(result.get('message', 'Processing failed'))
        
        return HttpResponse("OK")
        
    except Exception as e:
        logger.error(f"Generic webhook processing failed for {provider}: {str(e)}")
        return HttpResponseBadRequest("Processing failed")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook_test_endpoint(request):
    """Test endpoint for webhook development and debugging."""
    if not settings.DEBUG:
        return HttpResponseBadRequest("Test endpoint only available in debug mode")
    
    try:
        if request.method == 'GET':
            return HttpResponse("Webhook test endpoint is active")
        
        # POST request - log the payload
        payload = json.loads(request.body.decode('utf-8'))
        
        logger.info(f"Test webhook received: {payload}")
        
        # Create test webhook log
        WebhookLog.objects.create(
            provider='test',
            event_type=payload.get('event', 'test'),
            payload=payload,
            status='success',
            response_data={'message': 'Test webhook processed'},
            reference=payload.get('reference', 'test-ref')
        )
        
        return HttpResponse("Test webhook processed")
        
    except Exception as e:
        logger.error(f"Test webhook failed: {str(e)}")
        return HttpResponseBadRequest(f"Test failed: {str(e)}")