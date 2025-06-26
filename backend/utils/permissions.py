"""
Custom permission classes for Quickfund application
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Permission is only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners and admin users to access an object.
    """

    def has_object_permission(self, request, view, obj):
        # Permission is allowed to admin users
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Permission is allowed to the owner of the object
        return obj.owner == request.user


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission for user objects - allow users to edit their own profile
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the user themselves
        return obj == request.user


class IsAuthenticatedOrCreateOnly(permissions.BasePermission):
    """
    Permission to allow unauthenticated users to create accounts,
    but require authentication for other operations.
    """

    def has_permission(self, request, view):
        # Allow POST requests (for registration) without authentication
        if request.method == 'POST':
            return True
        
        # Require authentication for all other methods
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    Regular users can only read.
    """

    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for admin users
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class IsPaymentOwner(permissions.BasePermission):
    """
    Custom permission for payment objects - only allow access to payment owner
    """

    def has_object_permission(self, request, view, obj):
        # Check if the payment belongs to the requesting user
        # This assumes the payment model has a 'user' field
        return obj.user == request.user


class IsLoanOwner(permissions.BasePermission):
    """
    Custom permission for loan objects - only allow access to loan owner
    """

    def has_object_permission(self, request, view, obj):
        # Check if the loan belongs to the requesting user
        # This assumes the loan model has a 'borrower' field
        return obj.borrower == request.user


class IsTransactionOwner(permissions.BasePermission):
    """
    Custom permission for transaction objects - only allow access to transaction owner
    """

    def has_object_permission(self, request, view, obj):
        # Check if the transaction belongs to the requesting user
        # This assumes the transaction model has a 'user' field
        return obj.user == request.user


class CanManagePayments(permissions.BasePermission):
    """
    Permission for users who can manage payments (admin or payment managers)
    """

    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            (request.user.is_staff or 
             request.user.is_superuser or 
             hasattr(request.user, 'can_manage_payments') and request.user.can_manage_payments)
        )