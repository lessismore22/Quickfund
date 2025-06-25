from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import Repayment, Transaction, PaymentMethod
from quickfund_api.loans.models import Loan


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'user', 'provider', 'account_number', 'account_name',
            'bank_name', 'is_default', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_verified', 'created_at']

    def validate_account_number(self, value):
        """Validate account number format"""
        if not value.isdigit():
            raise serializers.ValidationError("Account number must contain only digits")
        if len(value) != 10:
            raise serializers.ValidationError("Account number must be 10 digits")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'amount', 'currency', 'status', 
            'transaction_type', 'description', 'gateway_response',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'gateway_response', 'created_at', 'updated_at'
        ]

    def validate_amount(self, value):
        """Validate transaction amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError("Amount cannot exceed 1,000,000")
        return value


class RepaymentSerializer(serializers.ModelSerializer):
    """Serializer for loan repayments"""
    transaction = TransactionSerializer(read_only=True)
    loan_title = serializers.CharField(source='loan.title', read_only=True)
    borrower_name = serializers.CharField(source='loan.borrower.get_full_name', read_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'loan', 'loan_title', 'borrower_name', 'amount', 
            'payment_date', 'payment_method', 'transaction', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_amount(self, value):
        """Validate repayment amount"""
        if value <= 0:
            raise serializers.ValidationError("Repayment amount must be greater than zero")
        return value

    def validate_loan(self, value):
        """Validate loan exists and is active"""
        if not value:
            raise serializers.ValidationError("Loan is required")
        if value.status != 'ACTIVE':
            raise serializers.ValidationError("Can only make repayments for active loans")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        loan = attrs.get('loan')
        amount = attrs.get('amount')
        
        if loan and amount:
            # Check if repayment amount doesn't exceed remaining balance
            remaining_balance = loan.amount_borrowed - loan.amount_repaid
            if amount > remaining_balance:
                raise serializers.ValidationError({
                    'amount': f"Repayment amount cannot exceed remaining balance of {remaining_balance}"
                })
        
        return attrs


class RepaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating repayments"""
    payment_method_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'loan', 'amount', 'payment_method_id', 'notes'
        ]

    def validate_payment_method_id(self, value):
        """Validate payment method exists and belongs to user"""
        try:
            payment_method = PaymentMethod.objects.get(id=value)
            if payment_method.user != self.context['request'].user:
                raise serializers.ValidationError("Payment method does not belong to user")
            if not payment_method.is_verified:
                raise serializers.ValidationError("Payment method is not verified")
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method does not exist")

    def create(self, validated_data):
        """Create repayment with transaction"""
        payment_method_id = validated_data.pop('payment_method_id')
        payment_method = PaymentMethod.objects.get(id=payment_method_id)
        
        # Create transaction first
        transaction = Transaction.objects.create(
            amount=validated_data['amount'],
            currency='NGN',
            transaction_type='REPAYMENT',
            description=f"Loan repayment for {validated_data['loan'].title}",
            status='PENDING'
        )
        
        # Create repayment
        repayment = Repayment.objects.create(
            **validated_data,
            payment_method=payment_method,
            transaction=transaction,
            payment_date=timezone.now()
        )
        
        return repayment


class RepaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing repayments"""
    loan_title = serializers.CharField(source='loan.title', read_only=True)
    borrower_name = serializers.CharField(source='loan.borrower.get_full_name', read_only=True)
    transaction_status = serializers.CharField(source='transaction.status', read_only=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'loan', 'loan_title', 'borrower_name', 'amount',
            'payment_date', 'transaction_status', 'created_at'
        ]


class PaymentSummarySerializer(serializers.Serializer):
    """Serializer for payment summary statistics"""
    total_repayments = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_transactions = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    this_month_repayments = serializers.DecimalField(max_digits=12, decimal_places=2)


class PaymentScheduleSerializer(serializers.Serializer):
    """Serializer for payment schedule"""
    due_date = serializers.DateField()
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2)
    is_overdue = serializers.BooleanField()
    days_overdue = serializers.IntegerField()


class BulkRepaymentSerializer(serializers.Serializer):
    """Serializer for bulk repayments"""
    loan_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=50
    )
    amount_per_loan = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method_id = serializers.IntegerField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_loan_ids(self, value):
        """Validate all loan IDs exist and belong to user"""
        user = self.context['request'].user
        loans = Loan.objects.filter(id__in=value, borrower=user)
        
        if loans.count() != len(value):
            raise serializers.ValidationError("Some loans do not exist or don't belong to user")
        
        inactive_loans = loans.exclude(status='ACTIVE')
        if inactive_loans.exists():
            raise serializers.ValidationError("All loans must be active for bulk repayment")
        
        return value

    def validate_amount_per_loan(self, value):
        """Validate amount per loan"""
        if value <= 0:
            raise serializers.ValidationError("Amount per loan must be greater than zero")
        if value > Decimal('100000.00'):
            raise serializers.ValidationError("Amount per loan cannot exceed 100,000")
        return value