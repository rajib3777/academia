import sentry_sdk
import pytz
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError
from django.http import Http404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.exceptions import Throttled
from django.core.cache import cache
from django.utils.timezone import now

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def format_validation_errors(error_detail):
    """
    Format DRF ValidationError detail into a consistent list.
    """
    formatted_errors = []

    if isinstance(error_detail, dict):
        for field, errors in error_detail.items():
            if isinstance(errors, list):
                for error in errors:
                    formatted_errors.append({"field": field, "error": str(error)})
            else:
                formatted_errors.append({"field": field, "error": str(errors)})

    elif isinstance(error_detail, list):
        for error in error_detail:
            formatted_errors.append({"field": "non_field_errors", "error": str(error)})
    else:
        formatted_errors.append({"field": "non_field_errors", "error": str(errors)})

    return formatted_errors


def custom_exception_handler(exc, context):
    # Let DRF handle the exception first
    response = drf_exception_handler(exc, context)

    if settings.SENTRY and settings.SENTRY_DSN:
        # Log the exception to Sentry
        sentry_sdk.capture_exception(exc)

    # Explicitly handle Django Http404
    if isinstance(exc, Http404):
        return Response(
            {
                "message": "Not found",
                "errors": [{"field": "detail", "error": str(exc)}]
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if isinstance(exc, ValidationError):
        formatted = format_validation_errors(exc.detail)
        return Response(
            {
                "message": "Validation failed",
                "errors": formatted
            },
            status=response.status_code if response else status.HTTP_400_BAD_REQUEST
        )

    # For DRF or Django exceptions (e.g. NotFound, PermissionDenied, etc.)
    if response is not None:
        detail = response.data.get('detail') if isinstance(response.data, dict) else str(response.data)
        message = getattr(exc, 'default_detail', None)
        if not message:
            message = exc.__class__.__name__.replace('_', ' ').replace('Exception', '').replace('Error', '').title()

        return Response(
            {
                "message": str(message),
                "errors": [{"field": "detail", "error": str(detail)}]
            },
            status=response.status_code
        )
    
    # Fallback for unhandled 500 errors
    return Response(
        {
            "message": "Server error",
            "errors": [{"field": "non_field_errors", "error": "An unexpected error occurred."}]
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

def convert_date_to_dhaka(date_obj):
    dhaka_tz = pytz.timezone('Asia/Dhaka')
    date_dhaka = date_obj.astimezone(dhaka_tz)
    return date_dhaka.strftime('%Y-%m-%d')


def get_client_ip(request):
    """Extracts client IP address from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_contact_us_rate_limit(request):
    """Enforces a rate limit of 2 requests per IP per day."""
    client_ip = get_client_ip(request)
    cache_key = f"contact_us_{client_ip}_{now().date()}"
    request_count = cache.get(cache_key, 0)

    if request_count >= 2:
        raise Throttled(detail="You have reached the daily limit of 2 requests.")

    cache.set(cache_key, request_count + 1, timeout=86400)  # 24 hours


def check_student_signup_rate_limit(request):
    """Enforces a rate limit of 30 requests per IP per day."""
    client_ip = get_client_ip(request)
    cache_key = f"student_signup_{client_ip}_{now().date()}"
    request_count = cache.get(cache_key, 0)

    if request_count >= 30:
        raise Throttled(detail="You have reached the daily limit of 30 requests.")

    cache.set(cache_key, request_count + 1, timeout=86400)  # 24 hours