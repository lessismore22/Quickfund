from rest_framework import serializers
from .models import Notification, NotificationTemplate, NotificationPreference, NotificationLog


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'title', 'message', 'data', 'status',
            'status_display', 'priority', 'priority_display', 'is_read',
            'reference_type', 'reference_id', 'scheduled_at', 'sent_at',
            'read_at', 'created_at', 'updated_at', 'time_since_created'
        ]
        read_only_fields = [
            'id', 'user', 'sent_at', 'read_at', 'created_at', 'updated_at'
        ]
    
    def get_time_since_created(self, obj):
        """Get human readable time since creation"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        if obj.created_at:
            return timesince(obj.created_at, timezone.now())
        return None


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for notification lists"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'title', 'status', 'status_display',
            'is_read', 'priority', 'created_at'
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of notification IDs to mark as read"
    )
    
    def validate_notification_ids(self, value):
        """Validate that all notification IDs belong to the current user"""
        user = self.context['request'].user
        valid_ids = Notification.objects.filter(
            id__in=value, user=user
        ).values_list('id', flat=True)
        
        invalid_ids = set(value) - set(valid_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid notification IDs: {list(invalid_ids)}"
            )
        
        return value


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', read_only=True
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'subject', 'body_template',
            'available_variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_body_template(self, value):
        """Validate that the template is properly formatted"""
        import re
        
        # Check for unclosed template variables
        open_braces = value.count('{{')
        close_braces = value.count('}}')
        
        if open_braces != close_braces:
            raise serializers.ValidationError(
                "Template has unclosed variables. Ensure all {{ are matched with }}"
            )
        
        return value


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', read_only=True
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'is_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationPreferenceUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating notification preferences"""
    
    preferences = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        allow_empty=False
    )
    
    def validate_preferences(self, value):
        """Validate preference data structure"""
        required_fields = ['notification_type', 'channel', 'is_enabled']
        
        for pref in value:
            # Check required fields
            missing_fields = set(required_fields) - set(pref.keys())
            if missing_fields:
                raise serializers.ValidationError(
                    f"Missing required fields: {list(missing_fields)}"
                )
            
            # Validate notification_type
            valid_types = [choice[0] for choice in NotificationTemplate.NOTIFICATION_TYPES]
            if pref['notification_type'] not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid notification_type: {pref['notification_type']}"
                )
            
            # Validate channel
            valid_channels = [choice[0] for choice in NotificationTemplate.CHANNELS]
            if pref['channel'] not in valid_channels:
                raise serializers.ValidationError(
                    f"Invalid channel: {pref['channel']}"
                )
            
            # Validate is_enabled
            if not isinstance(pref['is_enabled'], bool):
                if pref['is_enabled'].lower() in ['true', '1', 'yes']:
                    pref['is_enabled'] = True
                elif pref['is_enabled'].lower() in ['false', '0', 'no']:
                    pref['is_enabled'] = False
                else:
                    raise serializers.ValidationError(
                        f"Invalid is_enabled value: {pref['is_enabled']}"
                    )
        
        return value


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for NotificationLog model"""
    
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    channel_display = serializers.CharField(
        source='get_channel_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    can_retry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'notification_title', 'channel',
            'channel_display', 'status', 'status_display', 'attempts',
            'max_attempts', 'provider_response', 'error_message',
            'last_attempt_at', 'can_retry', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'notification', 'attempts', 'last_attempt_at',
            'created_at', 'updated_at'
        ]


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    pending_notifications = serializers.IntegerField()
    failed_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    notifications_by_channel = serializers.DictField()
    recent_notifications = NotificationListSerializer(many=True)


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending notifications"""
    
    user_id = serializers.UUIDField(required=False)
    user_email = serializers.EmailField(required=False)
    notification_type = serializers.ChoiceField(
        choices=NotificationTemplate.NOTIFICATION_TYPES
    )
    channel = serializers.ChoiceField(choices=NotificationTemplate.CHANNELS)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    priority = serializers.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        default='normal'
    )
    scheduled_at = serializers.DateTimeField(required=False)
    reference_type = serializers.ChoiceField(
        choices=Notification.REFERENCE_TYPES,
        required=False
    )
    reference_id = serializers.CharField(max_length=255, required=False)
    
    def validate(self, attrs):
        """Validate that either user_id or user_email is provided"""
        user_id = attrs.get('user_id')
        user_email = attrs.get('user_email')
        
        if not user_id and not user_email:
            raise serializers.ValidationError(
                "Either user_id or user_email must be provided"
            )
        
        if user_id and user_email:
            raise serializers.ValidationError(
                "Provide either user_id or user_email, not both"
            )
        
        return attrs
    
    def validate_user_id(self, value):
        """Validate that user exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User with this ID does not exist")
        
        return value
    
    def validate_user_email(self, value):
        """Validate that user exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if value and not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist")
        
        return value