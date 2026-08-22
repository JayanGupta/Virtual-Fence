"""
Virtual Fence — Custom Exception Classes
Provides domain-specific exceptions with consistent error codes for API responses.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Base Exception
# ---------------------------------------------------------------------------
class VirtualFenceError(Exception):
    """Base exception for all Virtual Fence domain errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------
class ZoneNotFoundError(VirtualFenceError):
    """Raised when a requested zone does not exist."""

    def __init__(self, zone_id: str):
        super().__init__(
            message=f"Zone '{zone_id}' not found.",
            error_code="ZONE_NOT_FOUND",
        )
        self.zone_id = zone_id


class IncidentNotFoundError(VirtualFenceError):
    """Raised when a requested incident does not exist."""

    def __init__(self, incident_id: str):
        super().__init__(
            message=f"Incident '{incident_id}' not found.",
            error_code="INCIDENT_NOT_FOUND",
        )
        self.incident_id = incident_id


class CameraNotAvailableError(VirtualFenceError):
    """Raised when a requested camera is not available."""

    def __init__(self, camera_index: int):
        super().__init__(
            message=f"Camera {camera_index} is not available.",
            error_code="CAMERA_NOT_AVAILABLE",
        )
        self.camera_index = camera_index


class InvalidZoneError(VirtualFenceError):
    """Raised when zone data is invalid."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid zone: {reason}",
            error_code="INVALID_ZONE",
        )


class InvalidStatusError(VirtualFenceError):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, status: str):
        super().__init__(
            message=f"Invalid status: '{status}'. Must be ACKNOWLEDGED or RESOLVED.",
            error_code="INVALID_STATUS",
        )


# ---------------------------------------------------------------------------
# Global Exception Handlers (registered on the FastAPI app)
# ---------------------------------------------------------------------------
async def virtual_fence_error_handler(request: Request, exc: VirtualFenceError) -> JSONResponse:
    """Handle all VirtualFenceError subclasses with consistent JSON responses."""
    status_map = {
        "ZONE_NOT_FOUND": 404,
        "INCIDENT_NOT_FOUND": 404,
        "CAMERA_NOT_AVAILABLE": 404,
        "INVALID_ZONE": 400,
        "INVALID_STATUS": 400,
        "INTERNAL_ERROR": 500,
    }
    status_code = status_map.get(exc.error_code, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code,
            "detail": exc.message,
            "status_code": status_code,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
        },
    )
