"""Review Queue Schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.candidate import CandidateResponse


class ReviewQueueBase(BaseModel):
    link_id: str
    candidate_id: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EDITED
    reviewer: Optional[str] = None
    reviewer_comment: Optional[str] = None


class ReviewQueueResponse(ReviewQueueBase):
    review_id: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    # Contextual fields for UI
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    broken_url: Optional[str] = None
    failure_type: Optional[str] = None
    anchor_text: Optional[str] = None
    surrounding_context: Optional[str] = None
    section_heading: Optional[str] = None
    candidate: Optional[CandidateResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewDecisionRequest(BaseModel):
    decision: str  # APPROVE, REJECT, EDIT, NO_REPLACEMENT
    replacement_url: Optional[str] = None
    comment: Optional[str] = None
    reviewer: str = "HUMAN_OPERATOR"
