from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import AbstractUser as CustomUser
from .validators import validate_bvn, validate_phone_number


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email', 'phone_number', 'first_name', 'last_name',
            'bvn', 'date_of_birth', 'address', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'bvn': {'validators': [validate_bvn]},
            'phone_number': {'validators': [validate_phone_number]},
        }

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate user credentials"""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include email and password.'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    full_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'phone_number', 'first_name', 'last_name',
            'full_name', 'bvn', 'date_of_birth', 'age', 'address',
            'is_verified', 'credit_score', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'is_verified', 'credit_score', 
            'date_joined', 'last_login'
        ]

    def validate_bvn(self, value):
        """Validate BVN if changed"""
        if self.instance and self.instance.bvn != value:
            validate_bvn(value)
        return value

    def validate_phone_number(self, value):
        """Validate phone number if changed"""
        if self.instance and self.instance.phone_number != value:
            validate_phone_number(value)
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'address'
        ]

    def validate_phone_number(self, value):
        """Validate phone number"""
        validate_phone_number(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def save(self):
        """Update user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserVerificationSerializer(serializers.Serializer):
    """Serializer for user verification"""
    bvn = serializers.CharField(validators=[validate_bvn])
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_bvn(self, value):
        """Validate BVN belongs to current user"""
        user = self.context['request'].user
        if user.bvn != value:
            raise serializers.ValidationError(
                'BVN does not match your registered BVN.'
            )
        return value


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'phone_number', 'first_name', 'last_name',
            'full_name', 'bvn', 'date_of_birth', 'address', 'is_active',
            'is_verified', 'credit_score', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list view"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'full_name', 'is_active', 'is_verified',
            'credit_score', 'date_joined'
        ]