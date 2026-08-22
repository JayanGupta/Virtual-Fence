"""
Virtual Fence — SQLAlchemy ORM Models
Defines persistent schema for security zones and intrusion incidents.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ZoneModel(Base):
    """A user-defined spatial security zone (polygon or tripwire)."""

    __tablename__ = "zones"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(128), nullable=False)
    type = Column(String(16), nullable=False, default="POLYGON")  # POLYGON | TRIPWIRE
    points = Column(Text, nullable=False)  # JSON string of [[x,y], …] normalised [0,1]
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    incidents = relationship("IncidentModel", back_populates="zone", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_zones_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Zone {self.name!r} ({self.type})>"


class IncidentModel(Base):
    """A recorded intrusion breach event."""

    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=_uuid)
    zone_id = Column(String, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False, index=True)
    object_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    snapshot_path = Column(String(512), nullable=True)
    video_path = Column(String(512), nullable=True)
    status = Column(String(16), default="UNREAD", index=True)  # UNREAD | ACKNOWLEDGED | RESOLVED
    severity = Column(String(16), default="MEDIUM")  # LOW | MEDIUM | HIGH | CRITICAL
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    zone = relationship("ZoneModel", back_populates="incidents")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_zone_id", "zone_id"),
        Index("ix_incidents_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Incident {self.id[:8]} zone={self.zone_id[:8]} status={self.status}>"
