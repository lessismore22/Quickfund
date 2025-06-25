from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import Notification, NotificationTemplate, NotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'notification_type', 'channel',
        'status', 'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'channel', 'status', 'is_read',
        'created_at', 'user__is_active'
    ]
    search_fields = [
        'user__email', 'user__phone_number', 'title',
        'message', 'reference_id'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'user_link',
        'sent_at', 'read_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_link', 'notification_type', 'channel')
        }),
        ('Content', {
            'fields': ('title', 'message', 'data')
        }),
        ('Status', {
            'fields': ('status', 'is_read', 'priority')
        }),
        ('References', {
            'fields': ('reference_type', 'reference_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'read_at'),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    actions = ['mark_as_read', 'mark_as_unread', 'resend_notification']
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(
            is_read=False, 
            read_at=None
        )
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
    
    def resend_notification(self, request, queryset):
        from .tasks import send_notification
        count = 0
        for notification in queryset.filter(status__in=['failed', 'pending']):
            send_notification.delay(notification.id)
            count += 1
        self.message_user(request, f'{count} notifications queued for resending.')
    resend_notification.short_description = 'Resend selected notifications'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'notification_type', 'channel',
        'is_active', 'created_at'
    ]
    list_filter = [
        'notification_type', 'channel', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'subject', 'body_template']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'notification_type', 'channel', 'is_active')
        }),
        ('Template Content', {
            'fields': ('subject', 'body_template')
        }),
        ('Variables', {
            'fields': ('available_variables',),
            'description': 'JSON object defining available template variables'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    ordering = ['notification_type', 'channel', 'name']
    list_per_page = 25
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} templates activated.')
    activate_templates.short_description = 'Activate selected templates'
    
    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} templates deactivated.')
    deactivate_templates.short_description = 'Deactivate selected templates'


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'notification_link', 'channel', 'status',
        'attempts', 'last_attempt_at', 'created_at'
    ]
    list_filter = [
        'channel', 'status', 'created_at', 'last_attempt_at'
    ]
    search_fields = [
        'notification__user__email', 'notification__title',
        'provider_response', 'error_message'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'notification_link',
        'last_attempt_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification_link', 'channel', 'status')
        }),
        ('Delivery Details', {
            'fields': ('attempts', 'max_attempts', 'last_attempt_at')
        }),
        ('Provider Response', {
            'fields': ('provider_response', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    
    def notification_link(self, obj):
        if obj.notification:
            url = reverse('admin:notifications_notification_change', 
                         args=[obj.notification.id])
            return format_html('<a href="{}">{}</a>', 
                             url, obj.notification.title[:50])
        return '-'
    notification_link.short_description = 'Notification'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    actions = ['retry_failed_notifications']
    
    def retry_failed_notifications(self, request, queryset):
        from .tasks import retry_notification
        count = 0
        for log in queryset.filter(status='failed', attempts__lt=models.F('max_attempts')):
            retry_notification.delay(log.id)
            count += 1
        self.message_user(request, f'{count} failed notifications queued for retry.')
    retry_failed_notifications.short_description = 'Retry selected failed notifications'