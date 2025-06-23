from django.urls import path
from quickfund_api.notifications.views import (
    NotificationListView,
    NotificationDetailView,
    NotificationPreferencesView,
    # MarkNotificationReadView,
    # BroadcastNotificationView,
)

urlpatterns = [
    # Notification Management
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<uuid:notification_id>/', NotificationDetailView.as_view(), name='notification_detail'),
    # path('<uuid:notification_id>/read/', MarkNotificationReadView.as_view(), name='notification_mark_read'),
    # path('mark-all-read/', MarkNotificationReadView.as_view(), name='notification_mark_all_read'),
    
    # Notification Preferences
    path('preferences/', NotificationPreferencesView.as_view(), name='notification_preferences'),
    path('preferences/email/', NotificationPreferencesView.as_view(), name='notification_email_preferences'),
    path('preferences/sms/', NotificationPreferencesView.as_view(), name='notification_sms_preferences'),
    path('preferences/push/', NotificationPreferencesView.as_view(), name='notification_push_preferences'),
    
    # Notification Types
    path('unread/', NotificationListView.as_view(), name='notification_unread'),
    path('important/', NotificationListView.as_view(), name='notification_important'),
    
    # Admin Notifications
    # path('broadcast/', BroadcastNotificationView.as_view(), name='notification_broadcast'),
    # path('templates/', BroadcastNotificationView.as_view(), name='notification_templates'),
]