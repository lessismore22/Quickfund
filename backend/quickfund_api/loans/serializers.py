from rest_framework import serializers
from .models import Loan, CreditAssessment

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'tenure_days', 'purpose')

    def validate_amount(self, value):
        if value % 1000 != 0:
            raise serializers.ValidationError("Amount must be in multiples of ₦1,000")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class LoanDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    repayment_amount = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = (
            'id', 'user_name', 'amount', 'approved_amount', 'interest_rate',
            'tenure_days', 'purpose', 'status', 'credit_score', 'disbursed_at',
            'due_date', 'total_repayment', 'balance', 'repayment_amount',
            'days_remaining', 'created_at', 'updated_at'
        )

    def get_repayment_amount(self, obj):
        return obj.calculate_repayment_amount()

    def get_days_remaining(self, obj):
        if obj.due_date:
            from django.utils import timezone
            delta = obj.due_date - timezone.now().date()
            return delta.days
        return None


class LoanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('status', 'approved_amount', 'rejection_reason')

    def validate(self, attrs):
        if attrs.get('status') == 'approved' and not attrs.get('approved_amount'):
            raise serializers.ValidationError("Approved amount is required for approval")
        if attrs.get('status') == 'rejected' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required")
        return attrs
    
    
        class LoanSerializer(serializers.ModelSerializer):
        
            class Meta:
                model = Loan
                fields = [
                    'id', 'borrower', 'amount', 'interest_rate', 'term_months', 
                    'status', 'application_date', 'approval_date', 'disbursement_date',
                    'due_date', 'outstanding_balance', 'monthly_payment'
                ]
                read_only_fields = ['id', 'application_date', 'approval_date', 'disbursement_date']
            
            def validate_amount(self, value):
                """
                Validate loan amount
                """
                if value <= 0:
                    raise serializers.ValidationError("Loan amount must be greater than zero")
                return value
            
            def validate_interest_rate(self, value):
                """
                Validate interest rate
                """
                if value < 0 or value > 100:
                    raise serializers.ValidationError("Interest rate must be between 0 and 100")
                return value
            
            def validate_term_months(self, value):
                """
                Validate loan term
                """
                if value <= 0:
                    raise serializers.ValidationError("Loan term must be greater than zero")
                return value
            
            class LoanSerializer(serializers.Serializer):
                """Serializer for loan application data
                """
                id = serializers.IntegerField(read_only=True)
                borrower = serializers.CharField(max_length=100, read_only=True)
                amount = serializers.DecimalField(max_digits=12, decimal_places=2)
                interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
                term_months = serializers.IntegerField()
                status = serializers.CharField(max_length=20, read_only=True)
                application_date = serializers.DateTimeField(read_only=True)
                approval_date = serializers.DateTimeField(read_only=True, required=False)
                disbursement_date = serializers.DateTimeField(read_only=True, required=False)
                due_date = serializers.DateField(read_only=True, required=False)
                outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
                monthly_payment = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

            def validate_amount(self, value):
                if value <= 0:
                    raise serializers.ValidationError("Amount must be greater than zero")
                return value