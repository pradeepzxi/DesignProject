"""Candidate and Candidate Scoring Schemas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CandidateScoreBase(BaseModel):
    semantic_similarity: Optional[float] = None
    title_similarity: Optional[float] = None
    url_similarity: Optional[float] = None
    keyword_overlap: Optional[float] = None
    domain_score: Optional[float] = None
    content_quality_score: Optional[float] = None
    overall_score: float
    rank: Optional[int] = None
    explanation: Optional[str] = None


class CandidateScoreResponse(CandidateScoreBase):
    score_id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)


class CandidateBase(BaseModel):
    candidate_url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    content_text: Optional[str] = None
    domain: Optional[str] = None
    source: Optional[str] = None


class CandidateResponse(CandidateBase):
    candidate_id: str
    link_id: str
    retrieved_at: datetime
    score: Optional[CandidateScoreResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    link_id: str
    broken_url: str
    failure_type: str
    anchor_text: Optional[str] = None
    section_heading: Optional[str] = None
    document_title: Optional[str] = None
    candidates: List[CandidateResponse] = []
    top_candidate: Optional[CandidateResponse] = None
    decision: str  # AUTO_REPAIR, HUMAN_REVIEW, NO_REPLACEMENT
    confidence_score: float
    decision_reason: str
