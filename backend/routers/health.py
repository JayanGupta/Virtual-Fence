"""
Virtual Fence — Health Router
Health check and system status endpoints for monitoring and container orchestration.
"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import get_db
from backend.models import ZoneModel, IncidentModel
from backend.schemas import HealthResponse, SystemStatus
from backend.services.camera_service import camera_manager

router = APIRouter(prefix="/api/v1", tags=["Health"])

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Lightweight health check for load balancers and container orchestration."""
    settings = get_settings()
    uptime = time.time() - _start_time

    # Quick DB check
    db_status = "connected"
    try:
        from backend.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1" if hasattr(db, 'execute') else db.connection())
        db.close()
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        uptime_seconds=round(uptime, 1),
        cameras_active=len(camera_manager.engines),
        database=db_status,
    )


@router.get("/status", response_model=SystemStatus)
def system_status(db: Session = Depends(get_db)):
    """Detailed system status for monitoring dashboards."""
    settings = get_settings()
    uptime = time.time() - _start_time

    total_zones = db.query(ZoneModel).count()
    total_incidents = db.query(IncidentModel).count()
    total_targets = sum(e.telemetry["active_targets"] for e in camera_manager.engines.values())
    is_breach = any(e.telemetry["state"] == "BREACH" for e in camera_manager.engines.values())

    return SystemStatus(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        state="BREACH" if is_breach else "SECURE",
        total_cameras=len(camera_manager.available_cameras),
        active_targets=total_targets,
        total_zones=total_zones,
        total_incidents=total_incidents,
        uptime_seconds=round(uptime, 1),
    )
