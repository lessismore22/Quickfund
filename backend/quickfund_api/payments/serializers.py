from rest_framework import serializers
from decimal import Decimal

# Add your existing serializers here...

class RepaymentSerializer(serializers.Serializer):
    """
    Serializer for loan repayment data
    """
    loan_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_method = serializers.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('mobile_money', 'Mobile Money'),
        ]
    )
    reference = serializers.CharField(max_length=100, required=False)
    
    def validate_amount(self, value):
        """
        Validate that the repayment amount is positive
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

class InitiateRepaymentSerializer(serializers.Serializer):
    """
    Serializer for initiating a repayment transaction
    """
    loan_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_method = serializers.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('mobile_money', 'Mobile Money'),
        ]
    )
    return_url = serializers.URLField(required=False)
    webhook_url = serializers.URLField(required=False)
    
    def validate_loan_id(self, value):
        """
        Validate that the loan exists and belongs to the user
        """
        try:
            from quickfund_api.loans.models import Loan
            loan = Loan.objects.get(id=value)
            return value
        except Loan.DoesNotExist:
            raise serializers.ValidationError("Loan not found")
    
    def validate_amount(self, value):
        """
        Validate repayment amount
        """
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value