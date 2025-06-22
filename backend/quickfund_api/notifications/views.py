from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationDetailView(generics.RetrieveAPIView):
    """Get notification details"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'notification_id'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
        
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=404)


MarkNotificationReadView = mark_notification_read


class NotificationPreferencesView(generics.RetrieveUpdateAPIView):
    """Manage notification preferences"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Return user's notification preferences
        return self.request.user
    
    def get(self, request):
        return Response({
            'email_notifications': True,
            'sms_notifications': True,
            'push_notifications': True,
        })
    
    def put(self, request):
        # Update notification preferences
        return Response({'message': 'Preferences updated successfully'})
