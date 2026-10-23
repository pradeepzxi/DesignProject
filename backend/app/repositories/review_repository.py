"""Review Queue Repository."""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from backend.app.models.prompt2_placeholders import ReviewQueueItem, Candidate
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.document import Document


def get_utc_now():
    return datetime.now(timezone.utc)


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: str) -> Optional[ReviewQueueItem]:
        return (
            self.db.query(ReviewQueueItem)
            .options(
                joinedload(ReviewQueueItem.candidate).joinedload(Candidate.scores),
            )
            .filter(ReviewQueueItem.review_id == review_id)
            .first()
        )

    def get_by_link_id(self, link_id: str) -> Optional[ReviewQueueItem]:
        return (
            self.db.query(ReviewQueueItem)
            .filter(ReviewQueueItem.link_id == link_id)
            .first()
        )

    def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[ReviewQueueItem]:
        query = self.db.query(ReviewQueueItem).options(
            joinedload(ReviewQueueItem.candidate).joinedload(Candidate.scores)
        )
        if status:
            query = query.filter(ReviewQueueItem.review_status == status)
        return query.order_by(ReviewQueueItem.created_at.desc()).offset(skip).limit(limit).all()

    def enqueue(
        self,
        link_id: str,
        candidate_id: Optional[str],
        confidence_score: float,
    ) -> ReviewQueueItem:
        existing = self.get_by_link_id(link_id)
        if existing:
            existing.candidate_id = candidate_id
            existing.confidence_score = confidence_score
            existing.review_status = "PENDING"
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = ReviewQueueItem(
            link_id=link_id,
            candidate_id=candidate_id,
            confidence_score=confidence_score,
            review_status="PENDING",
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def resolve(
        self,
        review_id: str,
        decision: str,
        reviewer: str = "HUMAN_OPERATOR",
        comment: Optional[str] = None,
    ) -> Optional[ReviewQueueItem]:
        item = self.get_by_id(review_id)
        if item:
            item.review_status = decision  # APPROVED, REJECTED, EDITED
            item.reviewer = reviewer
            item.reviewer_comment = comment
            item.reviewed_at = get_utc_now()
            self.db.commit()
            self.db.refresh(item)
        return item
