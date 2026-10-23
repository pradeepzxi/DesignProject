"""Scan Run Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class ScanRun(Base):
    __tablename__ = "scan_runs"

    scan_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_links = Column(Integer, default=0, nullable=False)
    valid_links = Column(Integer, default=0, nullable=False)
    broken_links = Column(Integer, default=0, nullable=False)
    redirected_links = Column(Integer, default=0, nullable=False)
    failed_links = Column(Integer, default=0, nullable=False)
    scan_status = Column(
        String(30),
        default="IN_PROGRESS",
        nullable=False,
    )  # IN_PROGRESS, COMPLETED, FAILED

    # Relationship
    document = relationship("Document", back_populates="scan_runs")
