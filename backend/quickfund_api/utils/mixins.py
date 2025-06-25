"""
Reusable class mixins for the QuickCash application.

This module contains mixins that provide common functionality
for models, views, and serializers.
"""

import uuid
from datetime import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from .exceptions import ValidationError, BusinessLogicError

User = get_user_model()


class TimestampMixin(models.Model):
    """
    Mixin to add created_at and updated_at fields to models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    """
    Mixin to add UUID primary key to models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality to models.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class AuditMixin(models.Model):
    """
    Mixin to add audit fields to models.
    """
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True


class StatusMixin(models.Model):
    """
    Mixin to add status field with common choices.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    class Meta:
        abstract = True


class VersionMixin(models.Model):
    """
    Mixin to add versioning to models.
    """
    version = models.PositiveIntegerField(default=1)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)


class AddressMixin(models.Model):
    """
    Mixin to add address fields to models.
    """
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    
    class Meta:
        abstract = True
    
    @property
    def full_address(self):
        """Return the full formatted address."""
        parts = [
            self.street_address,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in parts if part])


class ContactMixin(models.Model):
    """
    Mixin to add contact information fields.
    """
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    class Meta:
        abstract = True


class MetadataMixin(models.Model):
    """
    Mixin to add metadata fields for storing additional information.
    """
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
    
    def set_metadata(self, key, value):
        """Set a metadata value."""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value
        self.save(update_fields=['metadata'])
    
    def get_metadata(self, key, default=None):
        """Get a metadata value."""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)


# View Mixins

class StandardResultsSetPagination:
    """
    Standard pagination configuration.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class FilterMixin:
    """
    Mixin to add filtering capabilities to views.
    """
    def get_filtered_queryset(self, queryset, filters):
        """Apply filters to queryset."""
        for field, value in filters.items():
            if value is not None:
                if field.endswith('__icontains'):
                    queryset = queryset.filter(**{field: value})
                elif field.endswith('__gte') or field.endswith('__lte'):
                    queryset = queryset.filter(**{field: value})
                else:
                    queryset = queryset.filter(**{field: value})
        return queryset


class SearchMixin:
    """
    Mixin to add search capabilities to views.
    """
    search_fields = []
    
    def get_search_queryset(self, queryset, search_term):
        """Apply search to queryset."""
        if not search_term or not self.search_fields:
            return queryset
        
        from django.db.models import Q
        query = Q()
        
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": search_term})
        
        return queryset.filter(query)


class BulkActionMixin:
    """
    Mixin to add bulk actions to viewsets.
    """
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """Bulk delete objects."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'No IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        count = self.get_queryset().filter(id__in=ids).count()
        self.get_queryset().filter(id__in=ids).delete()
        
        return Response(
            {'message': f'{count} items deleted successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update objects."""
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})
        
        if not ids:
            return Response(
                {'error': 'No IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not update_data:
            return Response(
                {'error': 'No update data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        count = self.get_queryset().filter(id__in=ids).update(**update_data)
        
        return Response(
            {'message': f'{count} items updated successfully'},
            status=status.HTTP_200_OK
        )


class ExportMixin:
    """
    Mixin to add export capabilities to views.
    """
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export data as CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.get_export_filename()}.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = self.get_export_fields()
        writer.writerow(headers)
        
        # Write data
        queryset = self.filter_queryset(self.get_queryset())
        for obj in queryset:
            row = []
            for field in headers:
                value = getattr(obj, field, '')
                if hasattr(value, 'strftime'):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                row.append(str(value))
            writer.writerow(row)
        
        return response
    
    def get_export_filename(self):
        """Get the filename for export."""
        return f"{self.get_queryset().model._meta.verbose_name_plural}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_export_fields(self):
        """Get the fields to export."""
        return [field.name for field in self.get_queryset().model._meta.fields]


class CacheMixin:
    """
    Mixin to add caching capabilities to views.
    """
    cache_timeout = 300  # 5 minutes
    cache_key_prefix = 'view_cache'
    
    def get_cache_key(self, *args, **kwargs):
        """Generate a cache key for the view."""
        key_parts = [
            self.cache_key_prefix,
            self.__class__.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        return ':'.join(key_parts)
    
    def get_cached_response(self, cache_key):
        """Get cached response if available."""
        from django.core.cache import cache
        return cache.get(cache_key)
    
    def cache_response(self, cache_key, response):
        """Cache the response."""
        from django.core.cache import cache
        cache.set(cache_key, response, self.cache_timeout)


class ValidationMixin:
    """
    Mixin to add validation helpers to views.
    """
    def validate_required_fields(self, data, required_fields):
        """Validate that required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
    
    def validate_data_types(self, data, field_types):
        """Validate data types for fields."""
        type_errors = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                type_errors.append(f"{field} must be of type {expected_type.__name__}")
        
        if type_errors:
            raise ValidationError('; '.join(type_errors))


class PermissionMixin:
    """
    Mixin to add permission checking to views.
    """
    required_permissions = []
    
    def check_permissions(self, request):
        """Check if user has required permissions."""
        if not self.required_permissions:
            return True
        
        if not request.user.is_authenticated:
            return False
        
        for permission in self.required_permissions:
            if not request.user.has_perm(permission):
                return False
        
        return True
    
    def permission_denied(self, request, message=None):
        """Handle permission denied."""
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(message or "You don't have permission to perform this action.")


class LoggingMixin:
    """
    Mixin to add logging capabilities to views.
    """
    def log_action(self, action, user=None, extra_data=None):
        """Log an action."""
        import logging
        logger = logging.getLogger(__name__)
        
        log_data = {
            'action': action,
            'user_id': user.id if user else None,
            'timestamp': datetime.now(),
            'view': self.__class__.__name__,
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        logger.info(f"Action: {action}", extra=log_data)


class ResponseMixin:
    """
    Mixin to standardize API responses.
    """
    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        """Return a standardized success response."""
        response_data = {
            'success': True,
            'message': message,
            'data': data,
        }
        return Response(response_data, status=status_code)
    
    def error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Return a standardized error response."""
        response_data = {
            'success': False,
            'message': message,
            'errors': errors,
        }
        return Response(response_data, status=status_code)
    
    def paginated_response(self, queryset, serializer_class, request):
        """Return a paginated response."""
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)