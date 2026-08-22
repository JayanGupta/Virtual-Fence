"""
Virtual Fence — Zone Router
REST API endpoints for security zone CRUD operations.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import ZoneCreate, ZoneOut
from backend.services import zone_service
from backend.services.camera_service import camera_manager

router = APIRouter(prefix="/api/v1/zones", tags=["Zones"])


@router.get("", response_model=List[ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    """Retrieve all security zones."""
    return zone_service.list_zones(db)


@router.post("", response_model=ZoneOut, status_code=201)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    """Create a new polygonal security zone."""
    return zone_service.create_zone(
        db=db,
        name=payload.name,
        zone_type=payload.type.value,
        points=payload.points,
        engine_reload_callback=camera_manager.reload_all_zones,
    )


@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    """Delete a security zone by ID."""
    zone_service.delete_zone(
        db=db,
        zone_id=zone_id,
        engine_reload_callback=camera_manager.reload_all_zones,
    )
    return None
