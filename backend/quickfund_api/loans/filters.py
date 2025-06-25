from datetime import timezone
import django_filters
from django.db.models import Q
from .models import Loan, LoanApplication


class LoanFilter(django_filters.FilterSet):
    """Filter for Loan model"""
    
    status = django_filters.ChoiceFilter(choices=Loan.STATUS_CHOICES)
    min_amount = django_filters.NumberFilter(field_name='principal_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='principal_amount', lookup_expr='lte')
    min_interest_rate = django_filters.NumberFilter(field_name='interest_rate', lookup_expr='gte')
    max_interest_rate = django_filters.NumberFilter(field_name='interest_rate', lookup_expr='lte')
    term_months = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    due_date_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    borrower = django_filters.CharFilter(field_name='borrower__email', lookup_expr='icontains')
    overdue = django_filters.BooleanFilter(method='filter_overdue')
    
    class Meta:
        model = Loan
        fields = [
            'status', 'min_amount', 'max_amount', 'min_interest_rate', 
            'max_interest_rate', 'term_months', 'created_after', 
            'created_before', 'due_date_after', 'due_date_before', 
            'borrower', 'overdue'
        ]
    
    def filter_overdue(self, queryset, name, value):
        """Filter overdue loans"""
        if value:
            return queryset.filter(
                status='ACTIVE',
                due_date__lt=timezone.now().date()
            )
        return queryset


class LoanApplicationFilter(django_filters.FilterSet):
    """Filter for LoanApplication model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]

    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('business', 'Business Loan'),
        ('education', 'Education Loan'),
        ('auto', 'Auto Loan'),
        ('mortgage', 'Mortgage'),
    ]

    status = django_filters.ChoiceFilter(choices=LoanApplication.STATUS_CHOICES)
    loan_type = django_filters.ChoiceFilter(choices=LoanApplication.LOAN_TYPE_CHOICES)
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    min_credit_score = django_filters.NumberFilter(field_name='credit_score', lookup_expr='gte')
    max_credit_score = django_filters.NumberFilter(field_name='credit_score', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    approved_after = django_filters.DateTimeFilter(field_name='approved_at', lookup_expr='gte')
    approved_before = django_filters.DateTimeFilter(field_name='approved_at', lookup_expr='lte')
    borrower = django_filters.CharFilter(field_name='borrower__email', lookup_expr='icontains')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = LoanApplication
        fields = [
            'status', 'loan_type', 'min_amount', 'max_amount', 
            'min_credit_score', 'max_credit_score', 'created_after', 
            'created_before', 'approved_after', 'approved_before', 
            'borrower', 'search'
        ]
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        return queryset.filter(
            Q(borrower__first_name__icontains=value) |
            Q(borrower__last_name__icontains=value) |
            Q(borrower__email__icontains=value) |
            Q(purpose__icontains=value)
        )
    