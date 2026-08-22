"""
Virtual Fence — Incident Router
REST API endpoints for incident management.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import IncidentOut, IncidentPatch
from backend.services import incident_service

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentOut])
def list_incidents(
    limit: Optional[int] = Query(None, ge=1, le=500, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(None, description="Filter by status"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    db: Session = Depends(get_db),
):
    """Retrieve incidents with optional filtering and pagination."""
    return incident_service.list_incidents(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        zone_id=zone_id,
    )


@router.patch("/{incident_id}", response_model=IncidentOut)
def patch_incident(
    incident_id: str,
    payload: IncidentPatch,
    db: Session = Depends(get_db),
):
    """Update the status of an incident (ACKNOWLEDGED or RESOLVED)."""
    return incident_service.patch_incident(
        db=db,
        incident_id=incident_id,
        status=payload.status.value,
    )
