"""Audit Log Schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    document_id: Optional[str] = None
    link_id: Optional[str] = None
    action_type: str
    old_url: Optional[str] = None
    new_url: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    confidence_score: Optional[float] = None
    actor: str = "SYSTEM"


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    audit_id: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
