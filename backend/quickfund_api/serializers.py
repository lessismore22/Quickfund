from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Loan
from .models import User

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name', 'password', 'password_confirm')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'bvn', 'is_verified', 'date_of_birth', 'address', 'monthly_income',
            'employment_status', 'created_at'
        )
        read_only_fields = ('id', 'email', 'is_verified', 'created_at')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

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