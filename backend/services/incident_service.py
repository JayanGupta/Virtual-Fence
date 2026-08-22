"""
Virtual Fence — Incident Service
Business logic for incident management and retrieval.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.exceptions import IncidentNotFoundError, InvalidStatusError
from backend.logging_config import get_logger
from backend.models import IncidentModel

logger = get_logger("services.incidents")


def list_incidents(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    status: Optional[str] = None,
    zone_id: Optional[str] = None,
) -> List[IncidentModel]:
    """Retrieve incidents with optional filtering and pagination."""
    settings = get_settings()
    if limit is None:
        limit = settings.MAX_INCIDENTS_RETURNED

    query = db.query(IncidentModel)

    if status:
        query = query.filter(IncidentModel.status == status)
    if zone_id:
        query = query.filter(IncidentModel.zone_id == zone_id)

    return (
        query
        .order_by(IncidentModel.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_incident(db: Session, incident_id: str) -> IncidentModel:
    """Retrieve a single incident by ID."""
    incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not incident:
        raise IncidentNotFoundError(incident_id)
    return incident


def patch_incident(db: Session, incident_id: str, status: str) -> IncidentModel:
    """Update the status of an incident."""
    valid_statuses = ("ACKNOWLEDGED", "RESOLVED")
    if status not in valid_statuses:
        raise InvalidStatusError(status)

    incident = get_incident(db, incident_id)
    old_status = incident.status
    incident.status = status
    db.commit()
    db.refresh(incident)

    logger.info(
        "Incident %s status changed: %s → %s",
        incident_id[:8],
        old_status,
        status,
    )
    return incident


def count_incidents(db: Session, status: Optional[str] = None) -> int:
    """Count total incidents, optionally filtered by status."""
    query = db.query(IncidentModel)
    if status:
        query = query.filter(IncidentModel.status == status)
    return query.count()
