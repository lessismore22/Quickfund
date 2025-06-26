import hashlib
import hmac
import logging
from pyexpat.errors import messages

# Set up logger for this module
logger = logging.getLogger(__name__)
from django.conf import settings
from django.urls import reverse
import requests
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin
from django.db.models import Sum, Q, Count, Avg
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime, timedelta
from decimal import Decimal

from quickfund_api.payments.forms import LoanRepaymentForm
from quickfund_api.loans import models

from .models import Payment, Repayment, Transaction, PaymentMethod, PaymentSchedule
from .serializers import (
    RepaymentSerializer, RepaymentCreateSerializer, RepaymentListSerializer,
    TransactionSerializer, PaymentMethodSerializer, PaymentSummarySerializer,
    PaymentScheduleSerializer, BulkRepaymentSerializer
)
from .services import PaymentProcessorService
from quickfund_api.loans.models import Loan
from utils.exceptions import PaymentProcessingError
from utils.permissions import IsOwnerOrReadOnly
from .services import get_payment_service, get_payment_processor_service
# from .forms import LoanRepaymentForm


class PaymentMethodViewSet(ModelViewSet):
    """ViewSet for managing payment methods"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return payment methods for current user"""
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create payment method for current user"""
        # If this is the first payment method, make it default
        is_first = not PaymentMethod.objects.filter(user=self.request.user).exists()
        serializer.save(user=self.request.user, is_default=is_first)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set payment method as default"""
        payment_method = self.get_object()
        
        # Remove default from other methods
        PaymentMethod.objects.filter(
            user=request.user, is_default=True
        ).update(is_default=False)
        
        # Set this as default
        payment_method.is_default = True
        payment_method.save()
        
        return Response({'status': 'Payment method set as default'})

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify payment method"""
        payment_method = self.get_object()
        
        try:
            # Use payment service to verify account
            service = PaymentProcessorService()
            verification_result = service.verify_account(
                payment_method.account_number,
                payment_method.bank_name
            )
            
            if verification_result['verified']:
                payment_method.is_verified = True
                payment_method.account_name = verification_result.get('account_name', payment_method.account_name)
                payment_method.save()
                
                return Response({
                    'status': 'verified',
                    'account_name': payment_method.account_name
                })
            else:
                return Response({
                    'status': 'verification_failed',
                    'message': verification_result.get('message', 'Account verification failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RepaymentViewSet(ModelViewSet):
    """ViewSet for managing loan repayments"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return repayments for current user's loans"""
        return Repayment.objects.filter(
            loan__borrower=self.request.user
        ).select_related('loan', 'transaction', 'payment_method')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return RepaymentCreateSerializer
        elif self.action == 'list':
            return RepaymentListSerializer
        return RepaymentSerializer

    def perform_create(self, serializer):
        """Create repayment and process payment"""
        repayment = serializer.save()
        
        try:
            # Process payment through payment service
            service = PaymentProcessorService()
            result = service.process_repayment(repayment)
            
            if result['success']:
                repayment.transaction.status = 'COMPLETED'
                repayment.transaction.gateway_response = result.get('response', {})
                repayment.transaction.save()
                
                # Update loan repaid amount
                loan = repayment.loan
                loan.amount_repaid += repayment.amount
                loan.save()
                
            else:
                repayment.transaction.status = 'FAILED'
                repayment.transaction.gateway_response = result.get('response', {})
                repayment.transaction.save()
                
        except PaymentProcessingError as e:
            repayment.transaction.status = 'FAILED'
            repayment.transaction.gateway_response = {'error': str(e)}
            repayment.transaction.save()

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment summary for user"""
        user_loans = Loan.objects.filter(borrower=request.user)
        repayments = Repayment.objects.filter(loan__in=user_loans)
        transactions = Transaction.objects.filter(repayment__in=repayments)
        
        # Calculate summary data
        total_repayments = repayments.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        transaction_stats = transactions.aggregate(
            total_count=Count('id'),
            successful=Count('id', filter=Q(status='COMPLETED')),
            failed=Count('id', filter=Q(status='FAILED')),
            pending=Count('id', filter=Q(status='PENDING'))
        )
        
        # This month repayments
        this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_repayments = repayments.filter(
            payment_date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        summary_data = {
            'total_repayments': total_repayments,
            'total_transactions': transaction_stats['total_count'],
            'successful_payments': transaction_stats['successful'],
            'failed_payments': transaction_stats['failed'],
            'pending_payments': transaction_stats['pending'],
            'this_month_repayments': this_month_repayments
        }
        
        serializer = PaymentSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def schedule(self, request):
        """Get payment schedule for user's active loans"""
        active_loans = Loan.objects.filter(
            borrower=request.user,
            status='ACTIVE'
        )
        
        schedule_data = []
        today = timezone.now().date()
        
        for loan in active_loans:
            # Calculate next payment due date based on loan terms
            if loan.repayment_schedule:
                # Parse repayment schedule if available
                for payment in loan.repayment_schedule:
                    due_date = datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
                    amount_due = Decimal(payment['amount'])
                    
                    is_overdue = due_date < today
                    days_overdue = (today - due_date).days if is_overdue else 0
                    
                    schedule_data.append({
                        'due_date': due_date,
                        'amount_due': amount_due,
                        'is_overdue': is_overdue,
                        'days_overdue': days_overdue
                    })
        
        # Sort by due date
        schedule_data.sort(key=lambda x: x['due_date'])
        
        serializer = PaymentScheduleSerializer(schedule_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_repayment(self, request):
        """Process bulk repayments for multiple loans"""
        serializer = BulkRepaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            loan_ids = serializer.validated_data['loan_ids']
            amount_per_loan = serializer.validated_data['amount_per_loan']
            payment_method_id = serializer.validated_data['payment_method_id']
            notes = serializer.validated_data.get('notes', '')
            
            try:
                payment_method = PaymentMethod.objects.get(
                    id=payment_method_id,
                    user=request.user
                )
                
                repayments_created = []
                
                for loan_id in loan_ids:
                    loan = get_object_or_404(Loan, id=loan_id, borrower=request.user)
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        amount=amount_per_loan,
                        currency='NGN',
                        transaction_type='REPAYMENT',
                        description=f"Bulk repayment for {loan.title}",
                        status='PENDING'
                    )
                    
                    # Create repayment
                    repayment = Repayment.objects.create(
                        loan=loan,
                        amount=amount_per_loan,
                        payment_method=payment_method,
                        transaction=transaction,
                        payment_date=timezone.now(),
                        notes=notes
                    )
                    
                    repayments_created.append(repayment)
                
                # Process all payments
                service = PaymentProcessorService()
                results = service.process_bulk_repayments(repayments_created)
                
                return Response({
                    'status': 'bulk_repayment_initiated',
                    'repayments_count': len(repayments_created),
                    'results': results
                })
                
            except PaymentMethod.DoesNotExist:
                return Response({
                    'error': 'Payment method not found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """ViewSet for viewing transactions"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return transactions for current user's repayments"""
        user_repayments = Repayment.objects.filter(
            loan__borrower=self.request.user
        )
        return Transaction.objects.filter(
            repayment__in=user_repayments
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed transaction"""
        transaction = self.get_object()
        
        if transaction.status != 'FAILED':
            return Response({
                'error': 'Only failed transactions can be retried'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Reset transaction status
            transaction.status = 'PENDING'
            transaction.save()
            
            # Get associated repayment
            repayment = transaction.repayment
            
            # Retry payment processing
            service = PaymentProcessorService()
            result = service.process_repayment(repayment)
            
            if result['success']:
                transaction.status = 'COMPLETED'
                transaction.gateway_response = result.get('response', {})
                transaction.save()
                
                # Update loan repaid amount
                loan = repayment.loan
                loan.amount_repaid += repayment.amount
                loan.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Transaction processed successfully'
                })
            else:
                transaction.status = 'FAILED'
                transaction.gateway_response = result.get('response', {})
                transaction.save()
                
                return Response({
                    'status': 'failed',
                    'message': 'Transaction failed again'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            transaction.status = 'FAILED'
            transaction.gateway_response = {'error': str(e)}
            transaction.save()
            
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get transaction statistics"""
        queryset = self.get_queryset()
        
        # Filter by date range if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                pass
        
        stats = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            successful_count=Count('id', filter=Q(status='COMPLETED')),
            failed_count=Count('id', filter=Q(status='FAILED')),
            pending_count=Count('id', filter=Q(status='PENDING'))
        )
        
        # Calculate success rate
        total = stats['total_count'] or 0
        success_rate = (stats['successful_count'] / total * 100) if total > 0 else 0
        
        return Response({
            'total_amount': stats['total_amount'] or Decimal('0.00'),
            'total_transactions': total,
            'successful_transactions': stats['successful_count'],
            'failed_transactions': stats['failed_count'],
            'pending_transactions': stats['pending_count'],
            'success_rate': round(success_rate, 2)
        })
    
    # /root/Quickfund/backend/quickfund_api/payments/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from decimal import Decimal
import json
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView

# Import the service functions instead of module-level instances


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    """Initialize a payment transaction"""
    try:
        data = request.data
        amount = Decimal(str(data.get('amount', 0)))
        email = data.get('email')
        provider = data.get('provider', 'paystack')
        
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({
                'status': 'error',
                'message': 'Amount must be greater than 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get service instance
        processor_service = get_payment_processor_service()
        
        # Initialize payment
        result = processor_service.initialize_payment(
            amount=amount,
            email=email,
            provider=provider,
            reference=data.get('reference'),
            callback_url=data.get('callback_url'),
            metadata=data.get('metadata', {})
        )
        
        if result['status'] == 'success':
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, reference):
    """Verify a payment transaction"""
    try:
        provider = request.GET.get('provider', 'paystack')
        
        # Get service instance
        processor_service = get_payment_processor_service()
        
        # Verify payment
        result = processor_service.verify_payment_transaction(reference, provider)
        
        if result['status'] == 'success':
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def payment_webhook(request, provider):
    """Handle payment webhooks"""
    try:
        # Get raw body and signature
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Paystack-Signature', '')
        
        if not signature:
            return HttpResponse('Missing signature', status=400)
        
        # Get service instance
        processor_service = get_payment_processor_service()
        
        # Handle webhook
        result = processor_service.handle_webhook(provider, payload, signature)
        
        if result['status'] == 'success':
            # Here you would typically update your database with the payment status
            # For example:
            # - Update Payment model
            # - Update Loan model if applicable
            # - Send notifications
            
            return HttpResponse('OK', status=200)
        else:
            return HttpResponse(f"Error: {result['message']}", status=400)
    
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_refund(request):
    """Process a refund"""
    try:
        data = request.data
        transaction_id = data.get('transaction_id')
        amount = data.get('amount')
        reason = data.get('reason', '')
        provider = data.get('provider', 'paystack')
        
        if not transaction_id:
            return Response({
                'status': 'error',
                'message': 'Transaction ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get service instance
        payment_service = get_payment_service()
        
        # Process refund
        refund_amount = Decimal(str(amount)) if amount else None
        result = payment_service.process_refund(provider, transaction_id, refund_amount, reason)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class PaymentInitiationView(LoginRequiredMixin, View):
        """
        Handle payment initiation - create payment record and redirect to payment gateway
        """
    
        def post(self, request):
            try:
                data = json.loads(request.body)
                amount = Decimal(data.get('amount'))
                payment_type = data.get('payment_type', 'general')  # general, loan_repayment, etc.
                loan_id = data.get('loan_id')  # if it's a loan repayment
    
                # Create payment record
                payment = Payment.objects.create(
                    user=request.user,
                    amount=amount,
                    payment_type=payment_type,
                    status='pending',
                    reference=self.generate_payment_reference(),
                    loan_id=loan_id if loan_id else None
                )
    
                # Initialize Paystack payment
                paystack_data = {
                    'amount': int(amount * 100),  # Paystack expects amount in kobo
                    'email': request.user.email,
                    'reference': payment.reference,
                    'callback_url': request.build_absolute_uri(
                        reverse('paystack_callback')
                    ),
                    'metadata': {
                        'payment_id': payment.id,
                        'user_id': request.user.id,
                        'payment_type': payment_type
                    }
                }
    
                response = self.initialize_paystack_payment(paystack_data)
    
                if response and response.get('status'):
                    payment.gateway_reference = response['data']['reference']
                    payment.save()
    
                    return JsonResponse({
                        'status': 'success',
                        'payment_url': response['data']['authorization_url'],
                        'reference': payment.reference
                    })
                else:
                    payment.status = 'failed'
                    payment.save()
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Failed to initialize payment'
                    }, status=400)
    
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
    
        def generate_payment_reference(self):
            """Generate unique payment reference"""
            import uuid
            return f"PAY_{uuid.uuid4().hex[:10]}"
    
        def initialize_paystack_payment(self, data):
            """Initialize payment with Paystack"""
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
    
            try:
                response = requests.post(url, json=data, headers=headers)
                return response.json()
            except requests.RequestException:
                return None


class PaymentVerificationView(LoginRequiredMixin, View):
    """
    Verify payment status from payment gateway
    """
    
    def get(self, request):
        reference = request.GET.get('reference')
        if not reference:
            return JsonResponse({
                'status': 'error',
                'message': 'Payment reference is required'
            }, status=400)
        
        try:
            payment = get_object_or_404(Payment, reference=reference, user=request.user)
            
            # Verify with Paystack
            verification_result = self.verify_paystack_payment(reference)
            
            if verification_result and verification_result.get('status'):
                data = verification_result['data']
                
                if data['status'] == 'success':
                    payment.status = 'completed'
                    payment.gateway_reference = data['reference']
                    payment.completed_at = datetime.now()
                    payment.save()
                    
                    # Process loan repayment if applicable
                    if payment.loan and payment.payment_type == 'loan_repayment':
                        self.process_loan_repayment(payment)
                    
                    return JsonResponse({
                        'status': 'success',
                        'payment': {
                            'id': payment.id,
                            'amount': str(payment.amount),
                            'status': payment.status,
                            'reference': payment.reference
                        }
                    })
                else:
                    payment.status = 'failed'
                    payment.save()
                    
                    return JsonResponse({
                        'status': 'failed',
                        'message': 'Payment was not successful'
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Could not verify payment'
                }, status=400)
                
        except Payment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Payment not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    def verify_paystack_payment(self, reference):
        """Verify payment with Paystack"""
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        }
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except requests.RequestException:
            return None
    
    def process_loan_repayment(self, payment):
        """Process loan repayment after successful payment"""
        loan = payment.loan
        loan.amount_paid += payment.amount
        loan.balance -= payment.amount
        
        if loan.balance <= 0:
            loan.status = 'paid'
            loan.paid_at = datetime.now()
        
        loan.save()
        
        # # Create payment history record
        # 
        (
        #     loan=loan,
        #     payment=payment,
        #     amount=payment.amount,
        #     payment_date=payment.completed_at
        )


@method_decorator(csrf_exempt, name='dispatch')
class PaystackCallbackView(View):
    """
    Handle Paystack webhook callbacks
    """
    
    def post(self, request):
        try:
            # Verify webhook signature
            signature = request.headers.get('x-paystack-signature')
            if not self.verify_webhook_signature(request.body, signature):
                return HttpResponse(status=400)
            
            data = json.loads(request.body)
            event = data.get('event')
            
            if event == 'charge.success':
                self.handle_successful_payment(data['data'])
            elif event == 'charge.failed':
                self.handle_failed_payment(data['data'])
            
            return HttpResponse(status=200)
            
        except Exception as e:
            return HttpResponse(status=400)
    
    def verify_webhook_signature(self, payload, signature):
        """Verify Paystack webhook signature"""
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def handle_successful_payment(self, data):
        """Handle successful payment webhook"""
        reference = data.get('reference')
        try:
            payment = Payment.objects.get(reference=reference)
            if payment.status == 'pending':
                payment.status = 'completed'
                payment.completed_at = datetime.now()
                payment.save()
                
                # Process loan repayment if applicable
                if payment.loan and payment.payment_type == 'loan_repayment':
                    self.process_loan_repayment(payment)
                    
        except Payment.DoesNotExist:
            pass
    
    def handle_failed_payment(self, data):
        """Handle failed payment webhook"""
        reference = data.get('reference')
        try:
            payment = Payment.objects.get(reference=reference)
            payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass
class PaymentMethodsView(LoginRequiredMixin, View):
    """
    Display available payment methods for a loan
    """
    
    def get(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, user=request.user)
        
        # Available payment methods
        payment_methods = [
            {
                'id': 'card',
                'name': 'Debit/Credit Card',
                'description': 'Pay with your debit or credit card',
                'icon': 'card'
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Transfer directly from your bank account',
                'icon': 'bank'
            },
            {
                'id': 'ussd',
                'name': 'USSD',
                'description': 'Pay using USSD code from your mobile phone',
                'icon': 'phone'
            }
        ]
        
        context = {
            'loan': loan,
            'payment_methods': payment_methods,
            'balance': loan.balance
        }
        
        return render(request, 'payments/payment_methods.html', context)


# class PaymentHistoryView(LoginRequiredMixin, ListView):
#     """
#     Display payment history for a specific loan
#     """
#     model = PaymentHistory
#     template_name = 'payments/payment_history.html'
#     context_object_name = 'payments'
#     paginate_by = 20
    
#     def get_queryset(self):
#         loan_id = self.kwargs['loan_id']
#         loan = get_object_or_404(Loan, id=loan_id, user=self.request.user)
#         return PaymentHistory.objects.filter(loan=loan).order_by('-payment_date')
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         loan_id = self.kwargs['loan_id']
#         context['loan'] = get_object_or_404(Loan, id=loan_id, user=self.request.user)
#         return context

class LoanRepaymentView(LoginRequiredMixin, View):
    """Handle loan repayment"""
    
    def get(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, user=request.user)
        form = LoanRepaymentForm(loan=loan)
        
        context = {
            'loan': loan,
            'form': form,
            'outstanding_balance': loan.outstanding_balance,
            'minimum_payment': loan.minimum_payment_amount
        }
        return render(request, 'payments/loan_repayment.html', context)
    
    def post(self, request, loan_id):
        loan = get_object_or_404(Loan, id=loan_id, user=request.user)
        form = LoanRepaymentForm(request.POST, loan=loan)
        
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            
            # Create repayment record
            # Generate unique payment reference
            import uuid
            reference = f"PAY_{uuid.uuid4().hex[:10]}"
            payment = Payment.objects.create(
                user=request.user,
                loan=loan,
                amount=amount,
                reference=reference,
                description=f'Loan repayment for loan #{loan.id}',
                status='pending',
                payment_method=payment_method
            )
            
            if payment_method == 'paystack':
                # Redirect to Paystack
                return redirect('payment_initiate')
            else:
                # Handle other payment methods
                messages.success(request, 'Repayment initiated successfully')
                return redirect('payment_history', loan_id=loan.id)
        
        context = {
            'loan': loan,
            'form': form,
            'outstanding_balance': loan.outstanding_balance
        }
        return render(request, 'payments/loan_repayment.html', context)


class UserPaymentHistoryView(LoginRequiredMixin, ListView):
    """
    Display all payment history for the authenticated user
    """
    model = Payment
    template_name = 'payments/user_payment_history.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        user_payments = Payment.objects.filter(user=self.request.user)
        context['total_payments'] = user_payments.filter(status='completed').count()
        context['total_amount'] = user_payments.filter(
            status='completed'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return context


class PaymentReceiptView(LoginRequiredMixin, DetailView):
    """
    Generate and display payment receipt
    """
    model = Payment
    template_name = 'payments/payment_receipt.html'
    context_object_name = 'payment'
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user, status='completed')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = self.get_object()
        
        context['receipt_number'] = f"RCP{payment.id:06d}"
        context['issue_date'] = datetime.now()
        
        return context
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Add option to download as PDF if requested
        if request.GET.get('format') == 'pdf':
            return self.generate_pdf_receipt()
        
        return response
    
    def generate_pdf_receipt(self):
        """Generate PDF receipt (requires reportlab or similar)"""
        # Implementation depends on your PDF generation library
        # This is a placeholder for PDF generation logic
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{self.get_object().id}.pdf"'
        
        # Generate PDF content here
        # You would use reportlab, weasyprint, or similar library
        
        return response


class PaymentRefundView(LoginRequiredMixin, View):
    """Handle payment refund requests"""
    
    def get(self, request, pk):
        payment = get_object_or_404(
            Payment, 
            id=pk, 
            user=request.user, 
            status='completed'
        )
        
        context = {
            'payment': payment,
            'can_refund': payment.can_be_refunded(),
            'refund_deadline': payment.refund_deadline()
        }
        return render(request, 'payments/payment_refund.html', context)
    
    def post(self, request, pk):
        payment = get_object_or_404(
            Payment, 
            id=pk, 
            user=request.user, 
            status='completed'
        )
        
        if not payment.can_be_refunded():
            messages.error(request, 'This payment cannot be refunded')
            return redirect('payment_receipt', pk=pk)
        
        reason = request.POST.get('reason', '')
        
        with transaction.atomic():
            # Create refund request
            payment.status = 'refund_requested'
            payment.refund_reason = reason
            payment.refund_requested_at = datetime.now()
            payment.save()
            
            # Process refund with Paystack (if applicable)
            if payment.payment_method == 'paystack' and payment.transaction_id:
                self.process_paystack_refund(payment)
        
        messages.success(request, 'Refund request submitted successfully')
        return redirect('user_payment_history')
    
    def process_paystack_refund(self, payment):
        """Process refund through Paystack API"""
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        refund_data = {
            'transaction': payment.transaction_id,
            'amount': int(payment.amount * 100)  # Convert to kobo
        }
        
        try:
            response = requests.post(
                'https://api.paystack.co/refund',
                data=json.dumps(refund_data),
                headers=headers
            )
            response_data = response.json()
            
            if response_data['status']:
                payment.refund_id = response_data['data']['id']
                payment.status = 'refunded'
                payment.save()
            
        except Exception as e:
            # Log error and handle appropriately
            pass

class PaymentScheduleView(LoginRequiredMixin, TemplateView):
        """View for displaying payment schedules"""
        template_name = 'payments/schedule.html'
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            
            # Get payment schedules for the current user/student
            if hasattr(self.request.user, 'student'):
                schedules = PaymentSchedule.objects.filter(
                    student=self.request.user.student
                ).order_by('due_date')
            else:
                schedules = PaymentSchedule.objects.none()
            
            context.update({
                'schedules': schedules,
                'total_amount': schedules.aggregate(
                    total=Sum('amount')
                )['total'] or 0,
                'pending_amount': schedules.filter(
                    status='pending'
                ).aggregate(
                    total=Sum('amount')
                )['total'] or 0
            })
            
            return context

class UpcomingPaymentsView(LoginRequiredMixin, ListView):
    """View for upcoming payments"""
    model = PaymentSchedule
    template_name = 'payments/upcoming.html'
    context_object_name = 'upcoming_payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PaymentSchedule.objects.filter(
            due_date__gte=timezone.now().date(),
            status__in=['pending', 'partial']
        ).order_by('due_date')
        
        # Filter by student if regular user
        if hasattr(self.request.user, 'student'):
            queryset = queryset.filter(student=self.request.user.student)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        upcoming = self.get_queryset()
        context.update({
            'total_upcoming': upcoming.count(),
            'total_amount': upcoming.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'next_7_days': upcoming.filter(
                due_date__lte=timezone.now().date() + timedelta(days=7)
            ).count()
        })
        
        return context

class OverduePaymentsView(LoginRequiredMixin, ListView):
    """View for overdue payments"""
    model = PaymentSchedule
    template_name = 'payments/overdue.html'
    context_object_name = 'overdue_payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PaymentSchedule.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=['pending', 'partial']
        ).order_by('due_date')
        
        # Filter by student if regular user
        if hasattr(self.request.user, 'student'):
            queryset = queryset.filter(student=self.request.user.student)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        overdue = self.get_queryset()
        context.update({
            'total_overdue': overdue.count(),
            'total_amount': overdue.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'oldest_overdue': overdue.first(),
        })
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(View):
    """Handle Paystack webhook notifications"""
    
    def post(self, request, *args, **kwargs):
        try:
            # Verify webhook signature
            signature = request.headers.get('X-Paystack-Signature')
            if not self._verify_signature(request.body, signature):
                logger.warning("Invalid Paystack webhook signature")
                return HttpResponse(status=400)
            
            # Parse webhook data
            payload = json.loads(request.body.decode('utf-8'))
            event = payload.get('event')
            data = payload.get('data', {})
            
            # Handle different webhook events
            if event == 'charge.success':
                self._handle_successful_payment(data)
            elif event == 'charge.failed':
                self._handle_failed_payment(data)
            elif event == 'transfer.success':
                self._handle_transfer_success(data)
            elif event == 'transfer.failed':
                self._handle_transfer_failed(data)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return HttpResponse(status=500)
    
    def _verify_signature(self, payload, signature):
        """Verify Paystack webhook signature"""
        if not signature:
            return False
            
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        computed_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, computed_signature)
    
    def _handle_successful_payment(self, data):
        """Handle successful payment webhook"""
        reference = data.get('reference')
        amount = Decimal(str(data.get('amount', 0))) / 100  # Convert from kobo
        
        try:
            # Find and update payment record
            payment = Payment.objects.get(reference=reference)
            payment.status = 'completed'
            payment.amount_paid = amount
            payment.paid_at = timezone.now()
            payment.save()
            
            # Update related schedule
            if hasattr(payment, 'schedule'):
                payment.schedule.status = 'paid'
                payment.schedule.save()
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for reference: {reference}")
    
    def _handle_failed_payment(self, data):
        """Handle failed payment webhook"""
        reference = data.get('reference')
        
        try:
            payment = Payment.objects.get(reference=reference)
            payment.status = 'failed'
            payment.failure_reason = data.get('gateway_response', 'Payment failed')
            payment.save()
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for reference: {reference}")
    
    def _handle_transfer_success(self, data):
        """Handle successful transfer webhook"""
        # Implement transfer success logic
        pass
    
    def _handle_transfer_failed(self, data):
        """Handle failed transfer webhook"""
        # Implement transfer failure logic
        pass

class TransactionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view for listing all transactions"""
    model = Transaction
    template_name = 'payments/admin/transactions.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            'payment', 'student'
        ).order_by('-created_at')
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(student__user__email__icontains=search) |
                Q(student__registration_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics
        queryset = self.get_queryset()
        context.update({
            'total_transactions': queryset.count(),
            'total_amount': queryset.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'successful_count': queryset.filter(status='completed').count(),
            'failed_count': queryset.filter(status='failed').count(),
        })
        
        return context


class PaymentReconciliationView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin view for payment reconciliation"""
    template_name = 'payments/admin/reconciliation.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        date_from = self.request.GET.get('date_from', 
                                        (timezone.now() - timedelta(days=30)).date())
        date_to = self.request.GET.get('date_to', timezone.now().date())
        
        # Payment reconciliation data
        payments = Payment.objects.filter(
            created_at__date__range=[date_from, date_to]
        )
        
        transactions = Transaction.objects.filter(
            created_at__date__range=[date_from, date_to]
        )
        
        # Reconciliation summary
        context.update({
            'date_from': date_from,
            'date_to': date_to,
            'total_payments': payments.count(),
            'total_transactions': transactions.count(),
            'payments_amount': payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'transactions_amount': transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'successful_payments': payments.filter(status='completed').count(),
            'failed_payments': payments.filter(status='failed').count(),
            'pending_payments': payments.filter(status='pending').count(),
            'unmatched_payments': self._get_unmatched_payments(date_from, date_to),
        })
        
        return context
    
    def _get_unmatched_payments(self, date_from, date_to):
        """Get payments without matching transactions"""
        return Payment.objects.filter(
            created_at__date__range=[date_from, date_to],
            transaction__isnull=True
        )


class PaymentStatisticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin view for payment statistics"""
    template_name = 'payments/admin/statistics.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current period statistics
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Payment statistics
        current_month_payments = Payment.objects.filter(
            created_at__date__gte=current_month_start
        )
        
        last_month_payments = Payment.objects.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lt=current_month_start
        )
        
        context.update({
            # Current month stats
            'current_month_total': current_month_payments.count(),
            'current_month_amount': current_month_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'current_month_success_rate': self._calculate_success_rate(
                current_month_payments
            ),
            
            # Last month stats for comparison
            'last_month_total': last_month_payments.count(),
            'last_month_amount': last_month_payments.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'last_month_success_rate': self._calculate_success_rate(
                last_month_payments
            ),
            
            # Overall statistics
            'total_students_paid': Payment.objects.filter(
                status='completed'
            ).values('student').distinct().count(),
            
            'average_payment_amount': Payment.objects.filter(
                status='completed'
            ).aggregate(
                avg=Avg('amount')
            )['avg'] or 0,
            
            # Payment method breakdown
            'payment_methods': self._get_payment_method_stats(),
            
            # Daily payment trends (last 30 days)
            'daily_trends': self._get_daily_payment_trends(),
        })
        
        return context
    
    def _calculate_success_rate(self, payments):
        """Calculate payment success rate"""
        total = payments.count()
        if total == 0:
            return 0
        successful = payments.filter(status='completed').count()
        return round((successful / total) * 100, 2)
    
    def _get_payment_method_stats(self):
        """Get payment method statistics"""
        return Payment.objects.filter(
            status='completed'
        ).values('payment_method').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')
    
    def _get_daily_payment_trends(self):
        """Get daily payment trends for the last 30 days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        return Payment.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='completed'
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            amount=Sum('amount')
        ).order_by('day')
