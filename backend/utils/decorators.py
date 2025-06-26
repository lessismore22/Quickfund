"""
Custom decorators for the QuickCash application.

This module contains decorators for common functionality like
caching, rate limiting, logging, and permission checking.
"""

import functools
import json
import time
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework.response import Response
from rest_framework import status

from .exceptions import RateLimitError, AuthorizationError

logger = logging.getLogger(__name__)
User = get_user_model()


def validate_request_data(func):
    """
    Basic request data validation decorator
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    json.loads(request.body)
            except (json.JSONDecodeError, ValueError):
                return JsonResponse(
                    {'error': 'Invalid JSON data'}, 
                    status=400
                )
        return func(request, *args, **kwargs)
    return wrapper

def log_execution_time(func):
    """
    Decorator to log function execution time.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(
            f"Function {func.__name__} executed in {execution_time:.4f} seconds",
            extra={
                'function_name': func.__name__,
                'execution_time': execution_time,
                'args': args,
                'kwargs': kwargs,
            }
        )
        return result
    return wrapper


def rate_limit(max_requests=100, window=3600, key_func=None):
    """
    Rate limiting decorator.
    
    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds
        key_func: Function to generate cache key
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request)
            else:
                cache_key = f"rate_limit:{request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')}"
            
            # Get current request count
            current_requests = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_requests >= max_requests:
                raise RateLimitError(
                    message=f"Rate limit exceeded. Maximum {max_requests} requests per {window} seconds.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Increment counter
            cache.set(cache_key, current_requests + 1, window)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_staff(func):
    """
    Decorator to require staff permissions.
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise AuthorizationError(
                message="Staff permissions required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        return func(request, *args, **kwargs)
    return wrapper


def require_superuser(func):
    """
    Decorator to require superuser permissions.
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise AuthorizationError(
                message="Superuser permissions required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        return func(request, *args, **kwargs)
    return wrapper


def require_verified_user(func):
    """
    Decorator to require verified user.
    """
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise AuthorizationError(
                message="Authentication required",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        if not getattr(request.user, 'is_verified', False):
            raise AuthorizationError(
                message="User verification required",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return func(request, *args, **kwargs)
    return wrapper


def cache_result(timeout=300, key_prefix="cache"):
    """
    Decorator to cache function results.
    
    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        return wrapper
    return decorator


def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """
    Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {retries}/{max_retries}), "
                        f"retrying in {current_delay} seconds: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


def validate_json_request(required_fields=None):
    """
    Decorator to validate JSON request data.
    
    Args:
        required_fields: List of required field names
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'data'):
                return JsonResponse(
                    {'error': 'Invalid request format'},
                    status=400
                )
            
            if required_fields:
                missing_fields = [
                    field for field in required_fields
                    if field not in request.data
                ]
                if missing_fields:
                    return JsonResponse(
                        {
                            'error': 'Missing required fields',
                            'missing_fields': missing_fields
                        },
                        status=400
                    )
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def audit_trail(action=None, resource=None):
    """
    Decorator to create audit trail for actions.
    
    Args:
        action: Description of the action
        resource: Resource being acted upon
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            # Execute function
            result = func(request, *args, **kwargs)
            
            # Log audit trail
            audit_data = {
                'user_id': request.user.id if request.user.is_authenticated else None,
                'action': action or func.__name__,
                'resource': resource,
                'timestamp': datetime.now(),
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'request_data': getattr(request, 'data', {}),
            }
            
            logger.info(
                f"Audit Trail: {audit_data['action']}",
                extra=audit_data
            )
            
            return result
        return wrapper
    return decorator


def handle_exceptions(default_response=None):
    """
    Decorator to handle exceptions gracefully.
    
    Args:
        default_response: Default response to return on error
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {str(e)}")
                
                if default_response:
                    return default_response
                
                return JsonResponse(
                    {
                        'error': 'An unexpected error occurred',
                        'message': str(e)
                    },
                    status=500
                )
        return wrapper
    return decorator


def permission_required(permission):
    """
    Decorator to check specific permissions.
    
    Args:
        permission: Permission string to check
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise AuthorizationError(
                    message="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            
            if not request.user.has_perm(permission):
                raise AuthorizationError(
                    message=f"Permission required: {permission}",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# Class-based view decorators
require_staff_method = method_decorator(require_staff)
require_superuser_method = method_decorator(require_superuser)
require_verified_user_method = method_decorator(require_verified_user)
log_execution_time_method = method_decorator(log_execution_time)


def conditional_cache(timeout=300, condition_func=None):
    """
    Conditional caching decorator.
    
    Args:
        timeout: Cache timeout in seconds
        condition_func: Function to determine if caching should be applied
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            # Check condition
            if condition_func and not condition_func(request):
                return func(request, *args, **kwargs)
            
            # Apply caching
            cached_func = cache_page(timeout)(func)
            return cached_func(request, *args, **kwargs)
        return wrapper
    return decorator


def throttle_user(rate='100/hour'):
    """
    User-based throttling decorator.
    
    Args:
        rate: Throttle rate in format 'number/period'
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return func(request, *args, **kwargs)
            
            # Parse rate
            num_requests, period = rate.split('/')
            num_requests = int(num_requests)
            
            # Convert period to seconds
            period_seconds = {
                'second': 1,
                'minute': 60,
                'hour': 3600,
                'day': 86400,
            }.get(period, 3600)
            
            # Apply rate limiting
            rate_limited_func = rate_limit(
                max_requests=num_requests,
                window=period_seconds,
                key_func=lambda req: f"user_throttle:{req.user.id}"
            )(func)
            
            return rate_limited_func(request, *args, **kwargs)
        return wrapper
    return decorator