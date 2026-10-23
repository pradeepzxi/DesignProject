"""Audit Log Model.

Immutable audit trail recording all lifecycle actions, validation state transitions,
and forward-compatible remediation actions for experimental reproducibility.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)
    document_id = Column(
        String(36),
        ForeignKey("documents.document_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    link_id = Column(
        String(36),
        ForeignKey("links.link_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # DOCUMENT_UPLOADED, SCAN_STARTED, SCAN_COMPLETED, LINK_EXTRACTED, LINK_VALIDATED, LINK_BROKEN, LINK_REDIRECTED, VALIDATION_ERROR
    old_url = Column(Text, nullable=True)
    new_url = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    actor = Column(String(50), default="SYSTEM", nullable=False)

    # Relationships
    document = relationship("Document", back_populates="audit_logs")
    link = relationship("Link", back_populates="audit_logs")
