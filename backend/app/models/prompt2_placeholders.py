"""Database Models for Prompt 2 Autonomous Remediation and Research Experiments.

Defines schemas for:
- Candidate: Discovered replacement URLs and extracted page text
- CandidateScore: Multi-factor similarity and ranking scores with explanation
- Remediation: Audit record of link modifications and backup validations
- ReviewQueueItem: Human-in-the-loop review triage queue
- ExperimentRun: Empirical experiment configurations and benchmark results
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    link_id = Column(
        String(36),
        ForeignKey("links.link_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_url = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    snippet = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True)  # LOCAL_INTRANET, SITEMAP, CORP_ARCHIVE, WEB_SEARCH
    retrieved_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    link = relationship("Link", back_populates="candidates")
    scores = relationship("CandidateScore", back_populates="candidate", cascade="all, delete-orphan")
    reviews = relationship("ReviewQueueItem", back_populates="candidate")


class CandidateScore(Base):
    __tablename__ = "candidate_scores"

    score_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    candidate_id = Column(
        String(36),
        ForeignKey("candidates.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semantic_similarity = Column(Float, nullable=True)
    title_similarity = Column(Float, nullable=True)
    url_similarity = Column(Float, nullable=True)
    keyword_overlap = Column(Float, nullable=True)
    domain_score = Column(Float, nullable=True)
    content_quality_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=False, index=True)
    rank = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=True)

    # Relationship
    candidate = relationship("Candidate", back_populates="scores")


class Remediation(Base):
    __tablename__ = "remediations"

    remediation_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    link_id = Column(
        String(36),
        ForeignKey("links.link_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_url = Column(Text, nullable=False)
    new_url = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)
    action = Column(String(50), nullable=False)  # AUTO_REPAIRED, MANUAL_APPROVED, RECOMMENDATION_ONLY
    validation_result = Column(String(50), nullable=True)  # VERIFIED_WORKING, FAILED, PENDING
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    actor = Column(String(50), default="SYSTEM", nullable=False)  # SYSTEM, REVIEWER
    status = Column(String(50), default="COMPLETED", nullable=False)  # COMPLETED, FAILED, PENDING

    # Relationship
    link = relationship("Link", back_populates="remediations")


class ReviewQueueItem(Base):
    __tablename__ = "review_queue"

    review_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    link_id = Column(
        String(36),
        ForeignKey("links.link_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id = Column(
        String(36),
        ForeignKey("candidates.candidate_id", ondelete="SET NULL"),
        nullable=True,
    )
    confidence_score = Column(Float, nullable=True)
    review_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, EDITED
    reviewer = Column(String(100), nullable=True)
    reviewer_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    candidate = relationship("Candidate", back_populates="reviews")


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    experiment_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    experiment_name = Column(String(100), nullable=False)
    configuration = Column(JSON, nullable=False)
    dataset_version = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    results = Column(JSON, nullable=True)  # Precision, Recall, F1, MRR, Top-1, Top-3, Repair rate
    status = Column(String(50), default="COMPLETED", nullable=False)
