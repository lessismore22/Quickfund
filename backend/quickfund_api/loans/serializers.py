from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Loan, CreditAssessment, LoanApplication
from quickfund_api.users.serializers import UserProfileSerializer


class CreditAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for credit assessment"""
    
    class Meta:
        model = CreditAssessment
        fields = [
            'id', 'monthly_income', 'employment_status', 'employment_duration',
            'existing_debts', 'bank_statement_score', 'payment_history_score',
            'debt_to_income_ratio', 'overall_score', 'risk_level', 'created_at'
        ]
        read_only_fields = [
            'id', 'debt_to_income_ratio', 'overall_score', 'risk_level', 'created_at'
        ]

    def validate_monthly_income(self, value):
        """Validate monthly income"""
        if value <= 0:
            raise serializers.ValidationError("Monthly income must be greater than zero.")
        if value < Decimal('20000'):
            raise serializers.ValidationError("Minimum monthly income of ₦20,000 required.")
        return value

    def validate_employment_duration(self, value):
        """Validate employment duration"""
        if value < 0:
            raise serializers.ValidationError("Employment duration cannot be negative.")
        return value

    def validate_existing_debts(self, value):
        """Validate existing debts"""
        if value < 0:
            raise serializers.ValidationError("Existing debts cannot be negative.")
        return value

    def validate_bank_statement_score(self, value):
        """Validate bank statement score"""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Bank statement score must be between 0 and 100.")
        return value

    def validate_payment_history_score(self, value):
        """Validate payment history score"""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Payment history score must be between 0 and 100.")
        return value
    
class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'  # or specify specific fields like ['id', 'amount', 'status', etc.] 


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for loan application"""
    
    class Meta:
        model = Loan
        fields = [
            'amount', 'duration_months', 'purpose', 'collateral_description'
        ]

    def validate_amount(self, value):
        """Validate loan amount"""
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be greater than zero.")
        if value < Decimal('5000'):
            raise serializers.ValidationError("Minimum loan amount is ₦5,000.")
        if value > Decimal('500000'):
            raise serializers.ValidationError("Maximum loan amount is ₦500,000.")
        return value

    def validate_duration_months(self, value):
        """Validate loan duration"""
        if value < 1:
            raise serializers.ValidationError("Loan duration must be at least 1 month.")
        if value > 12:
            raise serializers.ValidationError("Maximum loan duration is 12 months.")
        return value

    def validate_purpose(self, value):
        """Validate loan purpose"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide a detailed loan purpose (minimum 10 characters).")
        return value

    def create(self, validated_data):
        """Create loan with current user"""
        user = self.context['request'].user
        
        # Check if user has any pending loans
        if Loan.objects.filter(user=user, status='PENDING').exists():
            raise serializers.ValidationError("You already have a pending loan application.")
        
        # Check if user has any active loans
        if Loan.objects.filter(user=user, status='ACTIVE').exists():
            raise serializers.ValidationError("You already have an active loan.")
        
        validated_data['user'] = user
        return super().create(validated_data)
    
class LoanApplicationCreateSerializer(serializers.ModelSerializer):
        class Meta:
            model = LoanApplication
            fields = ['applicant', 'amount', 'purpose']  # Only fields needed for creation
    
        def create(self, validated_data):
            # You can add custom creation logic here if needed
            return LoanApplication.objects.create(**validated_data)


class LoanDetailSerializer(serializers.ModelSerializer):
    """Serializer for loan details"""
    user = UserProfileSerializer(read_only=True)
    credit_assessment = CreditAssessmentSerializer(read_only=True)
    monthly_payment = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_since_application = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    next_payment_date = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'amount', 'duration_months', 'interest_rate',
            'monthly_payment', 'total_amount', 'amount_paid', 'balance',
            'purpose', 'collateral_description', 'status', 'rejection_reason',
            'application_date', 'approval_date', 'disbursement_date',
            'due_date', 'next_payment_date', 'is_overdue', 'days_since_application',
            'credit_assessment'
        ]

    def get_days_since_application(self, obj):
        """Get days since loan application"""
        return (timezone.now().date() - obj.application_date).days

    def get_is_overdue(self, obj):
        """Check if loan is overdue"""
        if obj.status == 'ACTIVE' and obj.due_date:
            return timezone.now().date() > obj.due_date
        return False

    def get_next_payment_date(self, obj):
        """Get next payment date"""
        if obj.status == 'ACTIVE':
            # This would typically be calculated based on payment schedule
            # For simplicity, using monthly intervals from disbursement date
            if obj.disbursement_date:
                from dateutil.relativedelta import relativedelta
                payments_made = obj.repayments.filter(status='COMPLETED').count()
                next_date = obj.disbursement_date + relativedelta(months=payments_made + 1)
                return next_date
        return None


class LoanListSerializer(serializers.ModelSerializer):
    """Serializer for loan list view"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    days_since_application = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id', 'user_name', 'user_email', 'amount', 'duration_months',
            'status', 'application_date', 'approval_date', 'due_date',
            'days_since_application', 'is_overdue'
        ]

    def get_days_since_application(self, obj):
        """Get days since loan application"""
        return (timezone.now().date() - obj.application_date).days

    def get_is_overdue(self, obj):
        """Check if loan is overdue"""
        if obj.status == 'ACTIVE' and obj.due_date:
            return timezone.now().date() > obj.due_date
        return False


class LoanApprovalSerializer(serializers.ModelSerializer):
    """Serializer for loan approval/rejection"""
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Loan
        fields = ['status', 'rejection_reason']

    def validate(self, attrs):
        """Validate approval/rejection data"""
        status = attrs.get('status')
        rejection_reason = attrs.get('rejection_reason')
        
        if status == 'REJECTED' and not rejection_reason:
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting a loan.'
            })
        
        if status == 'APPROVED' and rejection_reason:
            attrs.pop('rejection_reason')  # Remove rejection reason for approved loans
        
        return attrs


class LoanStatsSerializer(serializers.Serializer):
    """Serializer for loan statistics"""
    total_loans = serializers.IntegerField()
    pending_loans = serializers.IntegerField()
    approved_loans = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    completed_loans = serializers.IntegerField()
    rejected_loans = serializers.IntegerField()
    total_amount_disbursed = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount_repaid = serializers.DecimalField(max_digits=15, decimal_places=2)
    default_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class UserLoanSummarySerializer(serializers.Serializer):
    """Serializer for user loan summary"""
    total_loans = serializers.IntegerField()
    active_loans = serializers.IntegerField()
    completed_loans = serializers.IntegerField()
    total_borrowed = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_repaid = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    credit_score = serializers.IntegerField()
    can_apply_for_loan = serializers.BooleanField()