from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
# router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # User notification management
    # path('unread/', views.UnreadNotificationsView.as_view(), name='unread_notifications'),
    # path('mark-read/', views.MarkNotificationsReadView.as_view(), name='mark_read'),
    # path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    # path('<int:pk>/mark-read/', views.MarkSingleReadView.as_view(), name='mark_single_read'),
    
    # # Notification preferences
    # path('preferences/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    # path('preferences/update/', views.UpdatePreferencesView.as_view(), name='update_preferences'),
    
    # # Communication channels
    # path('send-sms/', views.SendSMSView.as_view(), name='send_sms'),
    # path('send-email/', views.SendEmailView.as_view(), name='send_email'),
    # path('send-push/', views.SendPushNotificationView.as_view(), name='send_push'),
    
    # # Bulk notifications (admin)
    # path('bulk-send/', views.BulkNotificationView.as_view(), name='bulk_send'),
    # path('broadcast/', views.BroadcastNotificationView.as_view(), name='broadcast'),
    
    # # Notification templates
    # path('templates/', views.NotificationTemplatesView.as_view(), name='notification_templates'),
    # path('templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='template_detail'),
    
    # # Notification statistics
    # path('statistics/', views.NotificationStatisticsView.as_view(), name='notification_statistics'),
    # path('delivery-status/', views.DeliveryStatusView.as_view(), name='delivery_status'),
    
    # Include router URLs
    path('', include(router.urls)),
]