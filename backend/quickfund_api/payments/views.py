from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Repayment, Transaction, PaymentMethod
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
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from decimal import Decimal
import json

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