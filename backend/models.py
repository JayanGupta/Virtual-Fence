"""
Virtual Fence — SQLAlchemy ORM Models
Defines persistent schema for security zones and intrusion incidents.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ZoneModel(Base):
    """A user-defined spatial security zone (polygon or tripwire)."""

    __tablename__ = "zones"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(128), nullable=False)
    type = Column(String(16), nullable=False, default="POLYGON")  # POLYGON | TRIPWIRE
    points = Column(Text, nullable=False)  # JSON string of [[x,y], …] normalised [0,1]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    incidents = relationship("IncidentModel", back_populates="zone", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Zone {self.name!r} ({self.type})>"


class IncidentModel(Base):
    """A recorded intrusion breach event."""

    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=_uuid)
    zone_id = Column(String, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    object_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    snapshot_path = Column(String(512), nullable=True)
    video_path = Column(String(512), nullable=True)
    status = Column(String(16), default="UNREAD")  # UNREAD | ACKNOWLEDGED | RESOLVED

    zone = relationship("ZoneModel", back_populates="incidents")

    def __repr__(self) -> str:
        return f"<Incident {self.id[:8]} zone={self.zone_id[:8]} status={self.status}>"
