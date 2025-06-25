from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Custom admin for CustomUser model"""
    
    list_display = (
        'email', 'full_name', 'phone_number', 'is_verified', 
        'is_active', 'credit_score', 'date_joined'
    )
    list_filter = (
        'is_active', 'is_verified', 'is_staff', 'is_superuser',
        'date_joined', 'verification_date'
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'bvn')
    ordering = ('-date_joined',)
    readonly_fields = (
        'date_joined', 'last_login', 'verification_date', 'age'
    )
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number', 
                'date_of_birth', 'age', 'address'
            )
        }),
        ('Verification Info', {
            'fields': ('bvn', 'is_verified', 'verification_date')
        }),
        ('Credit Info', {
            'fields': ('credit_score',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'bvn', 'date_of_birth', 'address', 'password1', 'password2'
            ),
        }),
    )
    
    def full_name(self, obj):
        """Display full name"""
        return obj.get_full_name() or '-'
    full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of users, only deactivation"""
        return False
    
    actions = ['activate_users', 'deactivate_users', 'verify_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} users were successfully activated.'
        )
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} users were successfully deactivated.'
        )
    deactivate_users.short_description = "Deactivate selected users"
    
    def verify_users(self, request, queryset):
        """Verify selected users"""
        from django.utils import timezone
        updated = queryset.filter(is_verified=False).update(
            is_verified=True,
            verification_date=timezone.now()
        )
        self.message_user(
            request, 
            f'{updated} users were successfully verified.'
        )
    verify_users.short_description = "Verify selected users"