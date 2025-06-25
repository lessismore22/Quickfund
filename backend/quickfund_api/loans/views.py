from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Loan, LoanApplication
from .serializers import (
    LoanSerializer, 
    LoanApplicationSerializer,
    LoanApprovalSerializer,
    LoanApplicationCreateSerializer
)
from .services import CreditScoringService
from .filters import LoanFilter
from .permissions import IsLoanOwnerOrAdmin, CanApproveLoan
from quickfund_api.utils.decorators import validate_request_data
# from utils.exceptions import LoanProcessingError

def validate_request_data(func):
    """decorator replacement"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class LoanApplicationViewSet(ModelViewSet):
    """
    ViewSet for handling loan applications
    """
    serializer_class = LoanApplicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'loan_type', 'created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return LoanApplication.objects.all()
        return LoanApplication.objects.filter(borrower=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LoanApplicationCreateSerializer
        elif self.action == 'approve':
            return LoanApprovalSerializer
        return LoanApplicationSerializer
    
    @validate_request_data
    def create(self, request, *args, **kwargs):
        """Create a new loan application"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user has pending applications
        pending_applications = LoanApplication.objects.filter(
            borrower=request.user,
            status='PENDING'
        ).count()
        
        if pending_applications >= 3:
            return Response(
                {'error': 'Maximum number of pending applications reached'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Perform credit scoring
            credit_service = CreditScoringService(request.user)
            credit_score = credit_service.calculate_score()
            
            loan_application = serializer.save(
                borrower=request.user,
                credit_score=credit_score
            )
            
            # Auto-approve if score is high enough
            if credit_score >= 700:
                loan_application.status = 'APPROVED'
                loan_application.approved_at = timezone.now()
                loan_application.save()
                
                # Create loan record
                Loan.objects.create(
                    borrower=request.user,
                    application=loan_application,
                    principal_amount=loan_application.amount,
                    interest_rate=loan_application.interest_rate,
                    term_months=loan_application.term_months,
                    monthly_payment=loan_application.calculate_monthly_payment(),
                    status='ACTIVE'
                )
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    @action(
        detail=True, 
        methods=['post'], 
        permission_classes=[CanApproveLoan],
        url_path='approve'
    )
    def approve(self, request, pk=None):
        """Approve a loan application"""
        application = self.get_object()
        
        if application.status != 'PENDING':
            return Response(
                {'error': 'Only pending applications can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Update application
            application.status = 'APPROVED'
            application.approved_at = timezone.now()
            application.approved_by = request.user
            application.approval_notes = serializer.validated_data.get('notes', '')
            application.save()
            
            # Create loan
            loan = Loan.objects.create(
                borrower=application.borrower,
                application=application,
                principal_amount=application.amount,
                interest_rate=serializer.validated_data.get(
                    'interest_rate', 
                    application.interest_rate
                ),
                term_months=application.term_months,
                monthly_payment=application.calculate_monthly_payment(),
                status='ACTIVE'
            )
            
            # Send notification (handled by signals)
        
        return Response(
            {'message': 'Loan application approved successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(
        detail=True, 
        methods=['post'], 
        permission_classes=[CanApproveLoan],
        url_path='reject'
    )
    def reject(self, request, pk=None):
        """Reject a loan application"""
        application = self.get_object()
        
        if application.status != 'PENDING':
            return Response(
                {'error': 'Only pending applications can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('reason', '')
        
        with transaction.atomic():
            application.status = 'REJECTED'
            application.rejected_at = timezone.now()
            application.rejected_by = request.user
            application.rejection_reason = rejection_reason
            application.save()
            
            # Send notification (handled by signals)
        
        return Response(
            {'message': 'Loan application rejected'},
            status=status.HTTP_200_OK
        )

class LoanCalculatorView(APIView):
    def post(self, request):
        # Your loan calculation logic here
        return Response({'message': 'Calculator endpoint'})

class LoanViewSet(ModelViewSet):
    """
    ViewSet for managing loans
    """
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated, IsLoanOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoanFilter
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Loan.objects.all()
        return Loan.objects.filter(borrower=self.request.user)
    
    @action(detail=True, methods=['get'], url_path='payment-schedule')
    def payment_schedule(self, request, pk=None):
        """Get loan payment schedule"""
        loan = self.get_object()
        schedule = loan.generate_payment_schedule()
        
        return Response({
            'loan_id': loan.id,
            'payment_schedule': schedule
        })
    
    @action(detail=True, methods=['post'], url_path='make-payment')
    def make_payment(self, request, pk=None):
        """Make a loan payment"""
        loan = self.get_object()
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'BANK_TRANSFER')
        
        if not amount:
            return Response(
                {'error': 'Payment amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if loan.status != 'ACTIVE':
            return Response(
                {'error': 'Cannot make payment on inactive loan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This would typically integrate with payment processor
        # For now, we'll create a payment record
        from quickfund_api.payments.models import Repayment
        
        with transaction.atomic():
            repayment = Repayment.objects.create(
                loan=loan,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=f"PAY_{timezone.now().strftime('%Y%m%d%H%M%S')}_{loan.id}",
                status='COMPLETED'
            )
            
            # Update loan balance
            loan.update_balance_after_payment(amount)
            
        return Response({
            'message': 'Payment processed successfully',
            'payment_id': repayment.id,
            'remaining_balance': loan.outstanding_balance
        })
    
    @action(detail=True, methods=['get'], url_path='repayment-history')
    def repayment_history(self, request, pk=None):
        """Get loan repayment history"""
        loan = self.get_object()
        repayments = loan.repayments.all().order_by('-created_at')
        
        from quickfund_api.payments.serializers import RepaymentSerializer
        serializer = RepaymentSerializer(repayments, many=True)
        
        return Response({
            'loan_id': loan.id,
            'repayments': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='my-loans')
    def my_loans(self, request):
        """Get current user's loans"""
        loans = Loan.objects.filter(borrower=request.user)
        serializer = self.get_serializer(loans, many=True)
        
        return Response({
            'count': loans.count(),
            'loans': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get loan summary for current user"""
        if request.user.is_staff:
            # Admin summary
            from django.db.models import Sum, Count, Avg
            
            summary = {
                'total_loans': Loan.objects.count(),
                'active_loans': Loan.objects.filter(status='ACTIVE').count(),
                'total_disbursed': Loan.objects.aggregate(
                    total=Sum('principal_amount')
                )['total'] or 0,
                'total_outstanding': Loan.objects.aggregate(
                    total=Sum('outstanding_balance')
                )['total'] or 0,
                'average_loan_amount': Loan.objects.aggregate(
                    avg=Avg('principal_amount')
                )['avg'] or 0,
            }
        else:
            # User summary
            user_loans = Loan.objects.filter(borrower=request.user)
            
            summary = {
                'total_loans': user_loans.count(),
                'active_loans': user_loans.filter(status='ACTIVE').count(),
                'total_borrowed': sum(loan.principal_amount for loan in user_loans),
                'total_outstanding': sum(loan.outstanding_balance for loan in user_loans),
                'total_paid': sum(loan.total_paid for loan in user_loans),
            }
        
        return Response(summary)
    
class EligibilityCheckView(APIView):
        def post(self, request):
            # Your eligibility check logic here
            return Response({"message": "Eligibility check endpoint"}, status=status.HTTP_200_OK)