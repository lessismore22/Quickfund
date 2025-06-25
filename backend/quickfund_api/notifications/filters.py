import django_filters
from django.db import models
from django.utils import timezone
from datetime import timedelta
from quickfund_api.notifications.models import Notification, NotificationTemplate


class NotificationFilter(django_filters.FilterSet):
    """Filter for Notification model"""
    
    # Status filters
    status = django_filters.ChoiceFilter(
        choices=Notification.STATUS_CHOICES,
        field_name='status',
        lookup_expr='exact'
    )
    
    # Type filters
    notification_type = django_filters.ChoiceFilter(
        choices=Notification.TYPE_CHOICES,
        field_name='notification_type',
        lookup_expr='exact'
    )
    
    # Priority filters
    priority = django_filters.ChoiceFilter(
        choices=Notification.PRIORITY_CHOICES,
        field_name='priority',
        lookup_expr='exact'
    )
    
    # Recipient filters
    recipient = django_filters.CharFilter(
        field_name='recipient',
        lookup_expr='icontains'
    )
    
    # Subject/Message filters
    subject = django_filters.CharFilter(
        field_name='subject',
        lookup_expr='icontains'
    )
    
    message = django_filters.CharFilter(
        field_name='message',
        lookup_expr='icontains'
    )
    
    # Date filters
    created_at = django_filters.DateFromToRangeFilter(
        field_name='created_at'
    )
    
    sent_at = django_filters.DateFromToRangeFilter(
        field_name='sent_at'
    )
    
    # Date shortcuts
    created_today = django_filters.BooleanFilter(
        method='filter_created_today',
        label='Created Today'
    )
    
    created_this_week = django_filters.BooleanFilter(
        method='filter_created_this_week',
        label='Created This Week'
    )
    
    created_this_month = django_filters.BooleanFilter(
        method='filter_created_this_month',
        label='Created This Month'
    )
    
    sent_today = django_filters.BooleanFilter(
        method='filter_sent_today',
        label='Sent Today'
    )
    
    # Failed notifications
    failed_notifications = django_filters.BooleanFilter(
        method='filter_failed_notifications',
        label='Failed Notifications'
    )
    
    # Pending notifications
    pending_notifications = django_filters.BooleanFilter(
        method='filter_pending_notifications',
        label='Pending Notifications'
    )
    
    # Retry eligible notifications
    retry_eligible = django_filters.BooleanFilter(
        method='filter_retry_eligible',
        label='Retry Eligible'
    )
    
    class Meta:
        model = Notification
        fields = [
            'status', 'notification_type', 'priority', 'recipient',
            'subject', 'message', 'created_at', 'sent_at'
        ]
    
    def filter_created_today(self, queryset, name, value):
        """Filter notifications created today"""
        if value:
            today = timezone.now().date()
            return queryset.filter(created_at__date=today)
        return queryset
    
    def filter_created_this_week(self, queryset, name, value):
        """Filter notifications created this week"""
        if value:
            week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
            return queryset.filter(created_at__date__gte=week_start)
        return queryset
    
    def filter_created_this_month(self, queryset, name, value):
        """Filter notifications created this month"""
        if value:
            month_start = timezone.now().replace(day=1).date()
            return queryset.filter(created_at__date__gte=month_start)
        return queryset
    
    def filter_sent_today(self, queryset, name, value):
        """Filter notifications sent today"""
        if value:
            today = timezone.now().date()
            return queryset.filter(sent_at__date=today)
        return queryset
    
    def filter_failed_notifications(self, queryset, name, value):
        """Filter failed notifications"""
        if value:
            return queryset.filter(status='failed')
        return queryset
    
    def filter_pending_notifications(self, queryset, name, value):
        """Filter pending notifications"""
        if value:
            return queryset.filter(status='pending')
        return queryset
    
    def filter_retry_eligible(self, queryset, name, value):
        """Filter notifications eligible for retry"""
        if value:
            return queryset.filter(
                status='failed',
                retry_count__lt=models.F('max_retries')
            )
        return queryset


class NotificationTemplateFilter(django_filters.FilterSet):
    """Filter for NotificationTemplate model"""
    
    # Name filter
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )
    
    # Type filters
    notification_type = django_filters.ChoiceFilter(
        choices=NotificationTemplate.TYPE_CHOICES,
        field_name='notification_type',
        lookup_expr='exact'
    )
    
    # Active filter
    is_active = django_filters.BooleanFilter(
        field_name='is_active'
    )
    
    # Subject filter
    subject = django_filters.CharFilter(
        field_name='subject',
        lookup_expr='icontains'
    )
    
    # Content filter
    content = django_filters.CharFilter(
        field_name='content',
        lookup_expr='icontains'
    )
    
    # Date filters
    created_at = django_filters.DateFromToRangeFilter(
        field_name='created_at'
    )
    
    updated_at = django_filters.DateFromToRangeFilter(
        field_name='updated_at'
    )
    
    # Language filter (if multilingual support is needed)
    language = django_filters.CharFilter(
        field_name='language',
        lookup_expr='exact'
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'notification_type', 'is_active', 'subject',
            'content', 'created_at', 'updated_at', 'language'
        ]


class NotificationStatsFilter(django_filters.FilterSet):
    """Filter for notification statistics and analytics"""
    
    # Date range for stats
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    # Group by options
    GROUP_BY_CHOICES = [
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('type', 'Notification Type'),
        ('status', 'Status'),
        ('priority', 'Priority'),
    ]
    
    group_by = django_filters.ChoiceFilter(
        choices=GROUP_BY_CHOICES,
        method='filter_group_by'
    )
    
    class Meta:
        model = Notification
        fields = ['date_from', 'date_to']
    
    def filter_group_by(self, queryset, name, value):
        """This method is for documentation - actual grouping logic should be in views"""
        return queryset


class NotificationDeliveryFilter(django_filters.FilterSet):
    """Filter for notification delivery tracking"""
    
    # Delivery status
    delivered = django_filters.BooleanFilter(
        method='filter_delivered'
    )
    
    # Bounce tracking
    bounced = django_filters.BooleanFilter(
        method='filter_bounced'
    )
    
    # Open tracking (for emails)
    opened = django_filters.BooleanFilter(
        method='filter_opened'
    )
    
    # Click tracking (for emails with links)
    clicked = django_filters.BooleanFilter(
        method='filter_clicked'
    )
    
    # Delivery time filters
    delivery_time_min = django_filters.NumberFilter(
        method='filter_delivery_time_min'
    )
    
    delivery_time_max = django_filters.NumberFilter(
        method='filter_delivery_time_max'
    )
    
    class Meta:
        model = Notification
        fields = []
    
    def filter_delivered(self, queryset, name, value):
        """Filter by delivery status"""
        if value:
            return queryset.filter(status='sent', sent_at__isnull=False)
        return queryset.filter(status__in=['pending', 'failed'])
    
    def filter_bounced(self, queryset, name, value):
        """Filter bounced notifications"""
        if value:
            return queryset.filter(
                status='failed',
                error_message__icontains='bounce'
            )
        return queryset
    
    def filter_opened(self, queryset, name, value):
        """Filter opened notifications (email tracking)"""
        # This would require additional fields in the model for tracking
        return queryset
    
    def filter_clicked(self, queryset, name, value):
        """Filter clicked notifications (email link tracking)"""
        # This would require additional fields in the model for tracking
        return queryset
    
    def filter_delivery_time_min(self, queryset, name, value):
        """Filter by minimum delivery time in seconds"""
        if value is not None:
            return queryset.extra(
                where=["EXTRACT(EPOCH FROM (sent_at - created_at)) >= %s"],
                params=[value]
            )
        return queryset
    
    def filter_delivery_time_max(self, queryset, name, value):
        """Filter by maximum delivery time in seconds"""
        if value is not None:
            return queryset.extra(
                where=["EXTRACT(EPOCH FROM (sent_at - created_at)) <= %s"],
                params=[value]
            )
        return queryset


# Utility functions for common filter operations
def get_notification_stats_queryset(queryset, group_by=None, date_from=None, date_to=None):
    """Get notification statistics queryset with grouping"""
    from django.db.models import Count, Q
    
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    
    if group_by == 'day':
        return queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending'))
        ).order_by('date')
    
    elif group_by == 'type':
        return queryset.values('notification_type').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending'))
        ).order_by('notification_type')
    
    elif group_by == 'status':
        return queryset.values('status').annotate(
            total=Count('id')
        ).order_by('status')
    
    elif group_by == 'priority':
        return queryset.values('priority').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            failed=Count('id', filter=Q(status='failed')),
            pending=Count('id', filter=Q(status='pending'))
        ).order_by('priority')
    
    return queryset


def get_failed_notifications_for_retry(max_age_hours=24):
    """Get failed notifications eligible for retry"""
    cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
    
    return Notification.objects.filter(
        status='failed',
        retry_count__lt=models.F('max_retries'),
        created_at__gte=cutoff_time
    ).order_by('priority', 'created_at')