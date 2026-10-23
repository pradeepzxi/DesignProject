"""Remediation Schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RemediationBase(BaseModel):
    link_id: str
    old_url: str
    new_url: str
    confidence_score: Optional[float] = None
    action: str  # AUTO_REPAIRED, MANUAL_APPROVED, RECOMMENDATION_ONLY
    validation_result: Optional[str] = None  # VERIFIED_WORKING, FAILED, PENDING
    actor: str = "SYSTEM"
    status: str = "COMPLETED"


class RemediationCreate(RemediationBase):
    pass


class RemediationResponse(RemediationBase):
    remediation_id: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    document_id: Optional[str] = None
    document_filename: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RemediationRequest(BaseModel):
    candidate_url: Optional[str] = None
    dry_run: bool = False
    reviewer: str = "SYSTEM"
