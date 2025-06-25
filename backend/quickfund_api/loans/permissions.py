from rest_framework import permissions
from django.contrib.auth.models import Group


class IsLoanOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of a loan or admin users to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Check if user is the borrower
        return obj.borrower == request.user


class CanApproveLoan(permissions.BasePermission):
    """
    Permission for users who can approve loans (loan officers, managers, admins).
    """
    
    def has_permission(self, request, view):
        # Superusers and staff have permission
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is in loan approval groups
        approval_groups = ['loan_officers', 'loan_managers', 'credit_analysts']
        user_groups = request.user.groups.values_list('name', flat=True)
        
        return any(group in approval_groups for group in user_groups)


class CanViewAllLoans(permissions.BasePermission):
    """
    Permission for users who can view all loans (not just their own).
    """
    
    def has_permission(self, request, view):
        # Read-only access for certain groups
        if request.method in permissions.SAFE_METHODS:
            if request.user.is_staff or request.user.is_superuser:
                return True
            
            view_groups = ['loan_officers', 'loan_managers', 'credit_analysts', 'auditors']
            user_groups = request.user.groups.values_list('name', flat=True)
            
            return any(group in view_groups for group in user_groups)
        
        # Write access only for staff
        return request.user.is_staff or request.user.is_superuser


class CanModifyLoan(permissions.BasePermission):
    """
    Permission for users who can modify loan details.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only staff and certain groups can modify loans
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        modify_groups = ['loan_managers', 'senior_loan_officers']
        user_groups = request.user.groups.values_list('name', flat=True)
        
        return any(group in modify_groups for group in user_groups)
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for authorized users
        return self.has_permission(request, view)