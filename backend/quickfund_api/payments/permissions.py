from django.contrib import admin
from django.db.models import Sum, Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
import csv
from .models import (
    PaymentGateway, PaymentMethod, Payment, Repayment,
    PaymentRefund, PaymentWebhook
)


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'is_active', 'test_mode', 'supported_currencies_display',
        'created_at', 'updated_at'
    ]
    list_filter = ['is_active', 'test_mode', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'test_mode')
        }),
        ('Configuration', {
            'fields': ('public_key', 'secret_key', 'webhook_url', 'supported_currencies')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def supported_currencies_display(self, obj):
        return ', '.join(obj.supported_currencies) if obj.supported_currencies else 'None'
    supported_currencies_display.short_description = 'Supported Currencies'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'gateway', 'method_type', 'last_four', 
        'is_default', 'is_active', 'created_at'
    ]
    list_filter = ['gateway', 'method_type', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'token', 'last_four']
    readonly_fields = ['token', 'created_at', 'updated_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'gateway', 'method_type')
        }),
        ('Payment Details', {
            'fields': ('token', 'last_four', 'expiry_month', 'expiry_year')
        }),
        ('Status', {
            'fields': ('is_default', 'is_active')
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'gateway_reference', 'user', 'amount_currency', 'status', 
        'gateway', 'initiated_at', 'confirmed_at'
    ]
    list_filter = [
        'status', 'gateway', 'currency', 'initiated_at', 
        'confirmed_at'
    ]
    search_fields = [
        'gateway_reference', 'user__email', 'user__phone_number',
        'description'
    ]
    readonly_fields = [
        'id', 'gateway_reference', 'gateway_response', 'initiated_at',
        'confirmed_at', 'failed_at', 'net_amount_display'
    ]
    raw_id_fields = ['user', 'loan', 'repayment', 'payment_method']
    date_hierarchy = 'initiated_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'user', 'loan', 'repayment', 'gateway_reference')
        }),
        ('Amount Details', {
            'fields': ('amount', 'currency', 'gateway_fee', 'processing_fee', 'net_amount_display')
        }),
        ('Gateway Information', {
            'fields': ('gateway', 'payment_method', 'gateway_response')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'failure_reason', 'description')
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'confirmed_at', 'failed_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['export_payments', 'mark_as_failed', 'retry_webhook_processing']

    def amount_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_currency.short_description = 'Amount'
    amount_currency.admin_order_field = 'amount'

    def net_amount_display(self, obj):
        return f"{obj.net_amount} {obj.currency}"
    net_amount_display.short_description = 'Net Amount'

    def export_payments(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payments.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'User', 'Amount', 'Currency', 'Status',
            'Gateway', 'Initiated At', 'Confirmed At'
        ])
        
        for payment in queryset:
            writer.writerow([
                payment.gateway_reference,
                payment.user.email,
                payment.amount,
                payment.currency,
                payment.status,
                payment.gateway.name if payment.gateway else '',
                payment.initiated_at,
                payment.confirmed_at or ''
            ])
        
        return response
    export_payments.short_description = 'Export selected payments'

    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='failed',
            failed_at=timezone.now(),
            failure_reason='Manually marked as failed by admin'
        )
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = 'Mark selected payments as failed'

    def retry_webhook_processing(self, request, queryset):
        # This would trigger webhook reprocessing for selected payments
        count = queryset.count()
        self.message_user(request, f'Webhook reprocessing queued for {count} payments.')
    retry_webhook_processing.short_description = 'Retry webhook processing'


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = [
        'loan', 'user', 'amount_currency', 'amount_paid_currency',
        'due_date', 'status', 'is_overdue_display', 'paid_date'
    ]
    list_filter = [
        'status', 'due_date', 'created_at', 'paid_date'
    ]
    search_fields = [
        'loan__id', 'user__email', 'user__phone_number', 'notes'
    ]
    readonly_fields = [
        'id', 'outstanding_amount_display', 'days_overdue_display',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['loan', 'user']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('id', 'loan', 'user')
        }),
        ('Repayment Details', {
            'fields': (
                'amount', 'principal_amount', 'interest_amount', 
                'fee_amount', 'amount_paid', 'late_fee'
            )
        }),
        ('Schedule & Status', {
            'fields': ('due_date', 'paid_date', 'status')
        }),
        ('Calculated Fields', {
            'fields': ('outstanding_amount_display', 'days_overdue_display'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_overdue', 'calculate_late_fees', 'export_repayments']

    def amount_currency(self, obj):
        return f"{obj.amount} NGN"
    amount_currency.short_description = 'Amount Due'
    amount_currency.admin_order_field = 'amount'

    def amount_paid_currency(self, obj):
        return f"{obj.amount_paid} NGN"
    amount_paid_currency.short_description = 'Amount Paid'
    amount_paid_currency.admin_order_field = 'amount_paid'

    def outstanding_amount_display(self, obj):
        return f"{obj.outstanding_amount} NGN"
    outstanding_amount_display.short_description = 'Outstanding'

    def days_overdue_display(self, obj):
        days = obj.days_overdue
        if days > 0:
            return format_html('<span style="color: red;">{} days</span>', days)
        return '0 days'
    days_overdue_display.short_description = 'Days Overdue'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue_display.short_description = 'Overdue'
    is_overdue_display.boolean = True

    def mark_as_overdue(self, request, queryset):
        updated = queryset.filter(
            due_date__lt=timezone.now().date(),
            status__in=['pending', 'partial']
        ).update(status='overdue')
        self.message_user(request, f'{updated} repayments marked as overdue.')
    mark_as_overdue.short_description = 'Mark overdue repayments'

    def calculate_late_fees(self, request, queryset):
        updated = 0
        for repayment in queryset.filter(status='overdue'):
            old_fee = repayment.late_fee
            new_fee = repayment.calculate_late_fee()
            if new_fee != old_fee:
                repayment.late_fee = new_fee