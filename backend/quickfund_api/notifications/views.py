from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    Notification, NotificationTemplate, NotificationPreference, NotificationLog
)
from .serializers import (
    NotificationSerializer, NotificationListSerializer, NotificationMarkReadSerializer,
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer, NotificationLogSerializer,
    NotificationStatsSerializer, SendNotificationSerializer
)
from .filters import NotificationFilter
from utils.permissions import IsOwnerOrAdmin
from utils.pagination import StandardResultsSetPagination


class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('user')


class NotificationDetailView(generics.RetrieveAPIView):
    """Retrieve notification details"""
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Mark notification as read when retrieved"""
        instance = self.get_object()
        if not instance.is_read:
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class NotificationMarkReadView(APIView):
    """Mark notifications as read"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = NotificationMarkReadSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            
            # Update notifications
            updated_count = Notification.objects.filter(
                id__in=notification_ids,
                user=request.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            return Response({
                'message': f'{updated_count} notifications marked as read',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'updated_count': updated_count
        })


class NotificationDeleteView(generics.DestroyAPIView):
    """Delete notification"""
    
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'message': 'Notification deleted successfully'})


class NotificationStatsView(APIView):
    """Get notification statistics"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Basic counts
        total_notifications = Notification.objects.filter(user=user).count()
        unread_notifications = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        pending_notifications = Notification.objects.filter(
            user=user, status='pending'
        ).count()
        failed_notifications = Notification.objects.filter(
            user=user, status='failed'
        ).count()
        
        # Notifications by type
        notifications_by_type = dict(
            Notification.objects.filter(user=user)
            .values('notification_type')
            .annotate(count=Count('id'))
            .values_list('notification_type', 'count')
        )
        
        # Notifications by channel
        notifications_by_channel = dict(
            Notification.objects.filter(user=user)
            .values('channel')
            .annotate(count=Count('id'))
            .values_list('channel', 'count')
        )
        
        # Recent notifications
        recent_notifications = Notification.objects.filter(user=user)[:5]
        
        stats_data = {
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'pending_notifications': pending_notifications,
            'failed_notifications': failed_notifications,
            'notifications_by_type': notifications_by_type,
            'notifications_by_channel': notifications_by_channel,
            'recent_notifications': recent_notifications
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)


class NotificationPreferenceListView(generics.ListAPIView):
    """List user notification preferences"""
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


class NotificationPreferenceUpdateView(APIView):
    """Update notification preferences"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = NotificationPreferenceUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            preferences_data = serializer.validated_data['preferences']
            user = request.user
            
            updated_count = 0
            created_count = 0
            
            for pref_data in preferences_data:
                preference, created = NotificationPreference.objects.update_or_create(
                    user=user,
                    notification_type=pref_data['notification_type'],
                    channel=pref_data['channel'],
                    defaults={'is_enabled': pref_data['is_enabled']}
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            return Response({
                'message': 'Preferences updated successfully',
                'updated_count': updated_count,
                'created_count': created_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationPreferenceDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update specific notification preference"""
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)


# Admin/Staff views
class NotificationTemplateListView(generics.ListCreateAPIView):
    """List and create notification templates (Admin only)"""
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'channel', 'is_active']
    search_fields = ['name', 'subject', 'body_template']
    ordering_fields = ['name', 'notification_type', 'created_at']
    ordering = ['notification_type', 'channel']


class NotificationTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete notification templates (Admin only)"""
    
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAdminUser]


class SendNotificationView(APIView):
    """Send notification to user (Admin only)"""
    
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            from django.contrib.auth import get_user_model
            from .tasks import send_notification
            
            User = get_user_model()
            data = serializer.validated_data
            
            # Get user
            if data.get('user_id'):
                user = get_object_or_404(User, id=data['user_id'])
            else:
                user = get_object_or_404(User, email=data['user_email'])
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                notification_type=data['notification_type'],
                channel=data['channel'],
                title=data['title'],
                message=data['message'],
                data=data.get('data', {}),
                priority=data.get('priority', 'normal'),
                scheduled_at=data.get('scheduled_at'),
                reference_type=data.get('reference_type'),
                reference_id=data.get('reference_id')
            )
            
            # Queue notification for sending
            if data.get('scheduled_at'):
                # Schedule for later
                send_notification.apply_async(
                    args=[notification.id],
                    eta=data['scheduled_at']
                )
            else:
                # Send immediately
                send_notification.delay(notification.id)
            
            return Response({
                'message': 'Notification queued for sending',
                'notification_id': notification.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationLogListView(generics.ListAPIView):
    """List notification logs (Admin only)"""
    
    queryset = NotificationLog.objects.all().select_related('notification')
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['channel', 'status', 'notification__notification_type']
    search_fields = ['notification__title', 'error_message']
    ordering_fields = ['created_at', 'last_attempt_at', 'attempts']
    ordering = ['-created_at']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return Response({'unread_count': count})


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def retry_failed_notifications(request):
    """Retry failed notifications"""
    from .tasks import retry_notification
    
    # Get failed notifications that can be retried
    failed_logs = NotificationLog.objects.filter(
        status='failed'
    ).filter(
        attempts__lt=models.F('max_attempts')
    )
    
    count = 0
    for log in failed_logs:
        retry_notification.delay(log.id)
        count += 1
    
    return Response({
        'message': f'{count} failed notifications queued for retry',
        'retry_count': count
    })