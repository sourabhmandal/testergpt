"""
Pydantic schemas for API responses
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DatabaseResponse(BaseModel):
    """
    Schema for database connection status
    """

    connected: bool = Field(..., description="Database connection status")
    type: str = Field(..., description="Type of the database (e.g., PostgreSQL, MySQL)")
    name: Optional[str] = Field(None, description="Name of the connected database")

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {"connected": True, "type": "PostgreSQL", "name": "testergpt_db"}
        }


class SystemInfoResponse(BaseModel):
    """
    Schema for system information including database details
    """

    python_version: str = Field(..., description="Python version")
    django_version: str = Field(..., description="Django version")
    platform: str = Field(..., description="Operating system platform")
    database_type: str = Field(
        ..., description="Type of the database (e.g., sqlite, postgresql)"
    )
    database_name: str = Field(..., description="Name of the connected database")

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {
                "python_version": "3.13.7",
                "django_version": "5.2.6",
                "platform": "macOS-14.0-arm64",
                "database_type": "sqlite",
                "database_name": "db.sqlite3",
            }
        }


class HealthCheckResponse(BaseModel):
    """
    Schema for health check API response
    """

    status: str = Field(..., description="Health status of the application")
    timestamp: datetime = Field(..., description="Timestamp of the health check")
    version: str = Field(default="1.0.0", description="Application version")
    database: str = Field(..., description="Database connection status")
    environment: str = Field(..., description="Current environment")
    details: SystemInfoResponse = Field(
        ..., description="System and database information"
    )

    class Config:
        """Pydantic configuration"""

        json_encoders = {datetime: lambda v: v.isoformat()}
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-09-20T10:30:00Z",
                "version": "1.0.0",
                "database": "connected",
                "environment": "development",
                "uptime": "2 hours, 15 minutes",
                "details": {
                    "python_version": "3.13.7",
                    "django_version": "5.2.6",
                    "platform": "macOS-14.0-arm64",
                    "database_type": "sqlite",
                    "database_name": "db.sqlite3",
                },
            }
        }


class ErrorResponse(BaseModel):
    """
    Schema for error responses
    """

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    timestamp: datetime = Field(..., description="Timestamp of the error")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional error details"
    )

    class Config:
        """Pydantic configuration"""

        json_encoders = {datetime: lambda v: v.isoformat()}
