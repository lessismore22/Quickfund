from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Repayment, Transaction, PaymentMethod


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'loan_link', 'amount', 'payment_method', 
        'status', 'transaction_reference', 'created_at'
    ]
    list_filter = [
        'status', 'payment_method', 'created_at', 
        'loan__status', 'loan__user__is_active'
    ]
    search_fields = [
        'transaction_reference', 'loan__user__email', 
        'loan__user__phone_number', 'loan__id'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'transaction_reference',
        'gateway_response', 'loan_link', 'user_link'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('loan_link', 'user_link', 'amount', 'payment_method')
        }),
        ('Payment Details', {
            'fields': ('status', 'transaction_reference', 'gateway_reference', 'notes')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',),
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
    
    def loan_link(self, obj):
        if obj.loan:
            url = reverse('admin:loans_loan_change', args=[obj.loan.id])
            return format_html('<a href="{}">{}</a>', url, obj.loan)
        return '-'
    loan_link.short_description = 'Loan'
    
    def user_link(self, obj):
        if obj.loan and obj.loan.user:
            url = reverse('admin:users_user_change', args=[obj.loan.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.loan.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'transaction_type', 'amount', 
        'status', 'reference', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'created_at',
        'user__is_active'
    ]
    search_fields = [
        'reference', 'user__email', 'user__phone_number',
        'gateway_reference', 'description'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'reference',
        'gateway_response', 'user_link'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_link', 'transaction_type', 'amount', 'description')
        }),
        ('Transaction Details', {
            'fields': ('status', 'reference', 'gateway_reference')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
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
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'method_type', 'provider',
        'is_default', 'is_active', 'created_at'
    ]
    list_filter = [
        'method_type', 'provider', 'is_default', 'is_active',
        'created_at', 'user__is_active'
    ]
    search_fields = [
        'user__email', 'user__phone_number', 'masked_details',
        'provider_reference'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'user_link',
        'provider_reference'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_link', 'method_type', 'provider')
        }),
        ('Payment Details', {
            'fields': ('masked_details', 'provider_reference', 'is_default', 'is_active')
        }),
        ('Metadata', {
            'fields': ('metadata',),
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
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    actions = ['mark_active', 'mark_inactive']
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} payment methods marked as active.')
    mark_active.short_description = 'Mark selected payment methods as active'
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} payment methods marked as inactive.')
    mark_inactive.short_description = 'Mark selected payment methods as inactive'