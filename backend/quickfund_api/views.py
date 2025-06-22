from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from backend.quickfund_api.services import LoanProcessingService
from quickfund_api.notifications import send_welcome_notification
from rest_framework.throttling import UserRateThrottle, throttle_classes
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import LoanApplicationSerializer, LoanDetailSerializer, LoanApprovalSerializer
from .models import Loan
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer,
    CustomTokenObtainPairSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send welcome SMS/Email

        send_welcome_notification.delay(user.id)
        
        return Response({
            'message': 'Registration successful',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)



class LoanApplicationThrottle(UserRateThrottle):
    scope = 'loan_application'

class LoanListView(generics.ListAPIView):
    serializer_class = LoanDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'purpose']

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Loan.objects.all()
        return Loan.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([LoanApplicationThrottle])
def apply_loan(request):
    """Apply for a new loan"""
    serializer = LoanApplicationSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        # Check if user has active loans
        active_loans = Loan.objects.filter(
            user=request.user, 
            status__in=['approved', 'disbursed', 'active']
        ).count()
        
        if active_loans >= 3:
            return Response({
                'error': 'You cannot have more than 3 active loans'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        loan = serializer.save()
        
        # Trigger credit scoring
        from .tasks import process_loan_application
        process_loan_application.delay(loan.id)
        
        return Response({
            'message': 'Loan application submitted successfully',
            'loan_id': loan.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def loan_detail(request, loan_id):
    """Get loan details"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Check permissions
    if request.user.role != 'admin' and loan.user != request.user:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = LoanDetailSerializer(loan)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def approve_loan(request, loan_id):
    """Approve or reject loan (Admin only)"""
    if request.user.role != 'admin':
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    loan = get_object_or_404(Loan, id=loan_id)
    serializer = LoanApprovalSerializer(loan, data=request.data, partial=True)
    
    if serializer.is_valid():
        updated_loan = serializer.save()
        
        # Process loan decision
        service = LoanProcessingService()
        service.process_loan_decision(updated_loan, request.user)
        
        return Response({
            'message': f'Loan {updated_loan.status} successfully'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
