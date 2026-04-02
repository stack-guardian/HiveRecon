"""Scan result model for persisted agent output."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from hiverecon.database import Base


class ScanResult(Base):
    """Stores normalized results emitted by individual scan stages."""

    __tablename__ = "scan_results"
    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('subdomain', 'port', 'endpoint', 'vuln')",
            name="ck_scan_results_agent_type",
        ),
        CheckConstraint(
            "severity IN ('high', 'medium', 'low', 'info')",
            name="ck_scan_results_severity",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    result_data = Column(JSON, nullable=False)
    severity = Column(String, nullable=False, default="info")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    scan = relationship("Scan")
