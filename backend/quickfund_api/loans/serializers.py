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