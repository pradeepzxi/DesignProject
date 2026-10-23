"""Link Model."""

import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Link(Base):
    __tablename__ = "links"

    link_id = Column(
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
    original_url = Column(Text, nullable=False)
    normalized_url = Column(Text, nullable=False, index=True)
    status = Column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )
    # Status Enum values:
    # VALID, BROKEN_404, BROKEN_4XX, SERVER_ERROR_5XX, TIMEOUT,
    # DNS_ERROR, CONNECTION_ERROR, REDIRECT, FORBIDDEN, UNAUTHORIZED,
    # INVALID_URL, UNKNOWN, PENDING
    status_code = Column(Integer, nullable=True)
    final_url = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    content_type = Column(String(100), nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    location_description = Column(String(255), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="links")
    context = relationship("LinkContext", back_populates="link", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="link")

    # Forward-compatible relationship placeholders for Prompt 2
    candidates = relationship("Candidate", back_populates="link", cascade="all, delete-orphan")
    remediations = relationship("Remediation", back_populates="link", cascade="all, delete-orphan")
