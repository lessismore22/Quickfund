from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import random

from .models import AbstractUser, CustomUser
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, PasswordChangeSerializer, UserVerificationSerializer,
    AdminUserSerializer, UserListSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .tasks import send_verification_sms, send_welcome_email
from ..utils.helpers import generate_otp


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            # Send welcome email asynchronously
            send_welcome_email.delay(user.email, user.first_name)
            
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Registration successful. Welcome email sent.'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login view"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        login(request, user)
        
        token, created = Token.objects.get_or_create(user=user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'message': 'Login successful.'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout view"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Delete user token
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        
        logout(request)
        return Response({
            'message': 'Logout successful.'
        }, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer
    
class ProfileUpdateView(APIView):
        permission_classes = [permissions.IsAuthenticated]
    
        def patch(self, request):
            user = request.user
    
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'username']
            for field in allowed_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
    
            user.save()
    
            return Response(
                {'message': 'Profile updated successfully'},
                status=status.HTTP_200_OK
            )


class PasswordChangeView(APIView):
    """Password change view"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Delete all user tokens to force re-login
        Token.objects.filter(user=request.user).delete()
        
        return Response({
            'message': 'Password changed successfully. Please login again.'
        }, status=status.HTTP_200_OK)


class RequestVerificationView(APIView):
    """Request user verification OTP"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        
        if user.is_verified:
            return Response({
                'message': 'User is already verified.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check rate limiting
        cache_key = f'verification_otp_{user.id}'
        if cache.get(cache_key):
            return Response({
                'error': 'OTP already sent. Please wait before requesting again.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate and cache OTP
        otp = generate_otp()
        cache.set(cache_key, otp, timeout=300)  # 5 minutes
        
        # Send OTP via SMS
        send_verification_sms.delay(user.phone_number, otp)
        
        return Response({
            'message': 'Verification OTP sent to your phone number.'
        }, status=status.HTTP_200_OK)
class EmailVerificationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Basic email verification placeholder
        return Response(
            {'message': 'Email verification functionality not implemented yet'}, 
            status=status.HTTP_200_OK
        )

class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Basic resend verification placeholder
        return Response(
            {'message': 'Verification email resent'}, 
            status=status.HTTP_200_OK
        )


class VerifyUserView(APIView):
    """Verify user with OTP"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UserVerificationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        otp = serializer.validated_data['otp']
        
        # Check OTP
        cache_key = f'verification_otp_{user.id}'
        cached_otp = cache.get(cache_key)
        
        if not cached_otp or cached_otp != otp:
            return Response({
                'error': 'Invalid or expired OTP.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user
        user.is_verified = True
        user.verification_date = timezone.now()
        user.save(update_fields=['is_verified', 'verification_date'])
        
        # Clear OTP from cache
        cache.delete(cache_key)
        
        return Response({
            'message': 'User verified successfully.',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)


# Admin Views
class AdminUserListView(generics.ListAPIView):
    """Admin view to list all users"""
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['is_active', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'credit_score']
    ordering = ['-date_joined']


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin view to manage individual users"""
    queryset = CustomUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        """Soft delete user by deactivating"""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({
            'message': 'User deactivated successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def activate_user(request, user_id):
    """Activate a deactivated user"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True
    user.save(update_fields=['is_active'])
    
    return Response({
        'message': 'User activated successfully.',
        'user': AdminUserSerializer(user).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def verify_user(request, user_id):
    """Admin verify user without OTP"""
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_verified = True
    user.verification_date = timezone.now()
    user.save(update_fields=['is_verified', 'verification_date'])
    
    return Response({
        'message': 'User verified successfully.',
        'user': AdminUserSerializer(user).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def user_stats(request):
    """Get user statistics"""
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    verified_users = CustomUser.objects.filter(is_verified=True).count()
    new_users_today = CustomUser.objects.filter(
        date_joined__date=timezone.now().date()
    ).count()
    new_users_this_week = CustomUser.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    return Response({
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'new_users_today': new_users_today,
        'new_users_this_week': new_users_this_week,
        'verification_rate': round((verified_users / total_users * 100), 2) if total_users > 0 else 0
    }, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        """Override to filter users based on permissions"""
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    