"""Document Model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # 'pdf' or 'docx'
    file_size = Column(Integer, nullable=False)  # in bytes
    upload_timestamp = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    processing_status = Column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )  # PENDING, PARSED, SCANNING, COMPLETED, FAILED
    document_title = Column(String(255), nullable=True)
    storage_path = Column(String(500), nullable=False)

    # Relationships
    links = relationship("Link", back_populates="document", cascade="all, delete-orphan")
    scan_runs = relationship("ScanRun", back_populates="document", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="document")
