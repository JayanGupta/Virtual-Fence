"""
Virtual Fence — Pydantic Request/Response Schemas
Centralized data validation with proper field constraints and OpenAPI examples.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ZoneType(str, Enum):
    POLYGON = "POLYGON"
    TRIPWIRE = "TRIPWIRE"


class IncidentStatus(str, Enum):
    UNREAD = "UNREAD"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class IncidentSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SystemState(str, Enum):
    SECURE = "SECURE"
    BREACH = "BREACH"


# ---------------------------------------------------------------------------
# Zone Schemas
# ---------------------------------------------------------------------------
class ZoneCreate(BaseModel):
    """Request schema for creating a security zone."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Human-readable name for the zone.",
        examples=["North Gate Perimeter"],
    )
    type: ZoneType = Field(
        default=ZoneType.POLYGON,
        description="Zone geometry type.",
    )
    points: List[List[float]] = Field(
        ...,
        min_length=3,
        description="Polygon vertices as [[x, y], …] normalised to [0, 1].",
        examples=[[[0.1, 0.2], [0.5, 0.2], [0.5, 0.8], [0.1, 0.8]]],
    )


class ZoneOut(BaseModel):
    """Response schema for a security zone."""

    id: str
    name: str
    type: str
    points: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Incident Schemas
# ---------------------------------------------------------------------------
class IncidentPatch(BaseModel):
    """Request schema for updating an incident status."""

    status: IncidentStatus = Field(
        ...,
        description="New status for the incident.",
        examples=[IncidentStatus.ACKNOWLEDGED],
    )


class IncidentOut(BaseModel):
    """Response schema for an incident record."""

    id: str
    zone_id: str
    object_id: int
    timestamp: datetime
    snapshot_path: Optional[str] = None
    video_path: Optional[str] = None
    status: str
    severity: str = "MEDIUM"

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Camera Schemas
# ---------------------------------------------------------------------------
class CameraOut(BaseModel):
    """Response schema for a camera device."""

    index: int
    name: str
    label: str


# ---------------------------------------------------------------------------
# Health & System Schemas
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(default="healthy", examples=["healthy"])
    version: str
    uptime_seconds: float
    cameras_active: int
    database: str = Field(default="connected", examples=["connected"])


class SystemStatus(BaseModel):
    """Response schema for detailed system status."""

    app_name: str
    version: str
    state: SystemState
    total_cameras: int
    active_targets: int
    total_zones: int
    total_incidents: int
    uptime_seconds: float


# ---------------------------------------------------------------------------
# Telemetry Schemas (for documentation; actual WS payloads)
# ---------------------------------------------------------------------------
class TargetTelemetry(BaseModel):
    id: int
    cx: int
    cy: int
    bbox: List[int]
    label: Optional[str] = None


class CameraTelemetry(BaseModel):
    camera_index: int
    camera_name: str
    active_targets: int
    state: SystemState
    targets: List[TargetTelemetry] = []


class TelemetryPayload(BaseModel):
    active_targets: int
    state: SystemState
    cameras: List[CameraTelemetry] = []
    alerts: Optional[List[dict]] = None


# ---------------------------------------------------------------------------
# Error Schema
# ---------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    """Standardised error response."""

    error: str
    detail: str
    status_code: int
    request_id: Optional[str] = None
