"""
Health check API views using Django REST Framework with functional views
"""

import sys
import platform
import django
from datetime import datetime, timezone
from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .schemas import (
    HealthCheckResponse,
    ErrorResponse,
    DatabaseResponse,
    SystemInfoResponse,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check API endpoint that returns application status
    """
    try:
        db_name = connection.settings_dict.get("NAME", "unknown")
        db_name_str = str(db_name) if db_name else "unknown"
        database_status = _check_database(db_name_str)
        system_info = _get_system_info(database_status)

        health_dto = HealthCheckResponse(
            status="healthy" if database_status.connected else "unhealthy",
            timestamp=datetime.now(timezone.utc),
            version=getattr(settings, "APP_VERSION", "1.0.0"),
            database="connected" if database_status.connected else "disconnected",
            environment=getattr(settings, "ENVIRONMENT", "development"),
            details=system_info,
        )
        response = Response(
            health_dto.model_dump(),
            status=status.HTTP_200_OK,
            headers={"ngrok-skip-browser-warning": "true"},
        )
        return response
    except Exception as e:
        error_dto = ErrorResponse(
            error="Health check failed",
            code="HEALTH_CHECK_ERROR",
            timestamp=datetime.now(timezone.utc),
            details={"error_message": str(e), "error_type": type(e).__name__},
        )
        response = Response(
            error_dto.model_dump(),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"ngrok-skip-browser-warning": "true"},
        )
        return response


def _check_database(db_name: str) -> DatabaseResponse:
    """
    Check database connectivity
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return DatabaseResponse(
                connected=True, type=connection.vendor, name=db_name
            )
    except Exception:
        return DatabaseResponse(connected=False, type=connection.vendor, name=db_name)


def _get_system_info(database_status: DatabaseResponse):
    """
    Get system information including database details
    """
    return SystemInfoResponse(
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        django_version=django.get_version(),
        platform=platform.platform(),
        database_type=database_status.type,
        database_name=database_status.name,
    )
