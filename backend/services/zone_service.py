"""
Virtual Fence — Zone Service
Business logic for security zone CRUD operations.
"""

import json
from typing import List, Optional, Callable

from sqlalchemy.orm import Session

from backend.exceptions import ZoneNotFoundError, InvalidZoneError
from backend.logging_config import get_logger
from backend.models import ZoneModel

logger = get_logger("services.zones")


def list_zones(db: Session) -> List[ZoneModel]:
    """Retrieve all zones ordered by creation date (newest first)."""
    return db.query(ZoneModel).order_by(ZoneModel.created_at.desc()).all()


def get_zone(db: Session, zone_id: str) -> ZoneModel:
    """Retrieve a single zone by ID."""
    zone = db.query(ZoneModel).filter(ZoneModel.id == zone_id).first()
    if not zone:
        raise ZoneNotFoundError(zone_id)
    return zone


def create_zone(
    db: Session,
    name: str,
    zone_type: str,
    points: list,
    engine_reload_callback: Optional[Callable] = None,
) -> ZoneModel:
    """Create a new security zone and notify vision engines."""
    # Validate polygon has at least 3 points
    if len(points) < 3:
        raise InvalidZoneError("Polygon must have at least 3 vertices.")

    # Validate all points are normalised [0, 1]
    for pt in points:
        if not (isinstance(pt, (list, tuple)) and len(pt) == 2):
            raise InvalidZoneError("Each point must be a [x, y] pair.")
        if not (0 <= pt[0] <= 1 and 0 <= pt[1] <= 1):
            raise InvalidZoneError("Point coordinates must be normalised to [0, 1].")

    zone = ZoneModel(
        name=name,
        type=zone_type,
        points=json.dumps(points),
        is_active=True,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)

    logger.info("Zone created: '%s' (%s, %d vertices)", name, zone_type, len(points))

    if engine_reload_callback:
        engine_reload_callback()

    return zone


def delete_zone(
    db: Session,
    zone_id: str,
    engine_reload_callback: Optional[Callable] = None,
) -> None:
    """Delete a security zone by ID."""
    zone = get_zone(db, zone_id)
    zone_name = zone.name
    db.delete(zone)
    db.commit()

    logger.info("Zone deleted: '%s' (id=%s)", zone_name, zone_id)

    if engine_reload_callback:
        engine_reload_callback()
