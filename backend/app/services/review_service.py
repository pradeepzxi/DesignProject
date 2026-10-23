"""Human Review Service.

Manages human-in-the-loop review queue for medium-confidence candidates,
processes reviewer approvals/rejections, and persists decisions for supervised learning.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.models.prompt2_placeholders import ReviewQueueItem
from backend.app.models.link import Link
from backend.app.repositories.review_repository import ReviewRepository
from backend.app.repositories.link_repository import LinkRepository
from backend.app.services.audit_service import AuditService
from backend.app.services.remediation_service import AutonomousRemediationService

FEEDBACK_DATASET_PATH = settings.EXPERIMENTS_DIR / "human_feedback_dataset.json"


def get_utc_now():
    return datetime.now(timezone.utc)


class HumanReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.link_repo = LinkRepository(db)
        self.remediation_service = AutonomousRemediationService(db)

    def submit_for_review(
        self,
        link_id: str,
        candidate_id: Optional[str],
        confidence_score: float,
    ) -> ReviewQueueItem:
        """Enqueue broken link for human triage."""
        item = self.review_repo.enqueue(
            link_id=link_id,
            candidate_id=candidate_id,
            confidence_score=confidence_score,
        )

        AuditService.log_event(
            db=self.db,
            action_type="HUMAN_REVIEW_REQUIRED",
            link_id=link_id,
            confidence_score=confidence_score,
            status="PENDING",
            reason=f"Queued for human review (Confidence: {round(confidence_score * 100, 1)}%)",
        )
        return item

    def get_review_items(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get review queue items enriched with source context and candidate details."""
        items = self.review_repo.get_all(status=status, skip=skip, limit=limit)
        enriched = []

        for it in items:
            link = self.link_repo.get_by_id(it.link_id)
            doc = link.document if link else None
            ctx = link.context if link else None
            cand = it.candidate

            cand_data = None
            if cand:
                top_score = cand.scores[0] if cand.scores else None
                cand_data = {
                    "candidate_id": cand.candidate_id,
                    "link_id": cand.link_id,
                    "candidate_url": cand.candidate_url,
                    "title": cand.title,
                    "snippet": cand.snippet,
                    "content_text": cand.content_text,
                    "domain": cand.domain,
                    "source": cand.source,
                    "retrieved_at": cand.retrieved_at,
                    "score": {
                        "score_id": top_score.score_id if top_score else "",
                        "candidate_id": cand.candidate_id,
                        "semantic_similarity": top_score.semantic_similarity if top_score else 0.0,
                        "title_similarity": top_score.title_similarity if top_score else 0.0,
                        "url_similarity": top_score.url_similarity if top_score else 0.0,
                        "keyword_overlap": top_score.keyword_overlap if top_score else 0.0,
                        "domain_score": top_score.domain_score if top_score else 0.0,
                        "content_quality_score": top_score.content_quality_score if top_score else 0.0,
                        "overall_score": top_score.overall_score if top_score else 0.0,
                        "rank": top_score.rank if top_score else 1,
                        "explanation": top_score.explanation if top_score else "",
                    } if top_score else None,
                }

            enriched.append({
                "review_id": it.review_id,
                "link_id": it.link_id,
                "candidate_id": it.candidate_id,
                "confidence_score": it.confidence_score,
                "review_status": it.review_status,
                "reviewer": it.reviewer,
                "reviewer_comment": it.reviewer_comment,
                "created_at": it.created_at,
                "reviewed_at": it.reviewed_at,
                "document_id": doc.document_id if doc else None,
                "document_title": doc.document_title or doc.filename if doc else None,
                "broken_url": link.original_url if link else None,
                "failure_type": link.status if link else None,
                "anchor_text": ctx.anchor_text if ctx else None,
                "surrounding_context": ctx.surrounding_text if ctx else None,
                "section_heading": ctx.section_heading if ctx else None,
                "candidate": cand_data,
            })

        return enriched

    async def resolve_review(
        self,
        review_id: str,
        decision: str,  # APPROVE, REJECT, EDIT, NO_REPLACEMENT
        replacement_url: Optional[str] = None,
        reviewer: str = "HUMAN_OPERATOR",
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process human reviewer decision, trigger remediation if approved, and save research feedback."""
        review_item = self.review_repo.get_by_id(review_id)
        if not review_item:
            raise ValueError(f"Review item {review_id} not found")

        link = self.link_repo.get_by_id(review_item.link_id)
        if not link:
            raise ValueError(f"Associated link {review_item.link_id} not found")

        # Determine target replacement URL
        target_url = replacement_url
        if not target_url and review_item.candidate:
            target_url = review_item.candidate.candidate_url

        remediation_result = None

        if decision in ("APPROVE", "EDIT"):
            if not target_url:
                raise ValueError("No valid replacement URL specified for approval")

            # Execute remediation
            remediation_result = await self.remediation_service.apply_remediation(
                link_id=link.link_id,
                replacement_url=target_url,
                confidence_score=review_item.confidence_score or 1.0,
                actor=reviewer,
                action="MANUAL_APPROVED",
            )

            AuditService.log_event(
                db=self.db,
                action_type="HUMAN_APPROVED",
                document_id=link.document_id,
                link_id=link.link_id,
                old_url=link.original_url,
                new_url=target_url,
                status="COMPLETED",
                confidence_score=review_item.confidence_score,
                reason=f"Approved by {reviewer}: {comment or 'Manual review verified'}",
                actor=reviewer,
            )
        elif decision == "REJECT":
            AuditService.log_event(
                db=self.db,
                action_type="HUMAN_REJECTED",
                document_id=link.document_id,
                link_id=link.link_id,
                old_url=link.original_url,
                status="REJECTED",
                confidence_score=review_item.confidence_score,
                reason=f"Rejected by {reviewer}: {comment or 'Incorrect candidate'}",
                actor=reviewer,
            )

        # Update Review record in DB
        resolved_item = self.review_repo.resolve(
            review_id=review_id,
            decision=decision,
            reviewer=reviewer,
            comment=comment,
        )

        # Append to Phase 18 Human-in-the-Loop Feedback Dataset for Supervised Learning
        self._record_feedback_dataset_entry(
            review_item=resolved_item,
            link=link,
            decision=decision,
            replacement_url=target_url,
            reviewer=reviewer,
            comment=comment,
        )

        return {
            "success": True,
            "review_id": review_id,
            "decision": decision,
            "reviewer": reviewer,
            "remediation": remediation_result,
        }

    @staticmethod
    def _record_feedback_dataset_entry(
        review_item: ReviewQueueItem,
        link: Link,
        decision: str,
        replacement_url: Optional[str],
        reviewer: str,
        comment: Optional[str],
    ):
        """Append review decisions to research feedback dataset."""
        try:
            entries = []
            if FEEDBACK_DATASET_PATH.exists():
                with open(FEEDBACK_DATASET_PATH, "r", encoding="utf-8") as f:
                    entries = json.load(f)

            top_score = review_item.candidate.scores[0] if review_item.candidate and review_item.candidate.scores else None
            entry = {
                "review_id": review_item.review_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "link_id": link.link_id,
                "broken_url": link.original_url,
                "anchor_text": link.context.anchor_text if link.context else "",
                "section_heading": link.context.section_heading if link.context else "",
                "candidate_url": replacement_url,
                "predicted_score": review_item.confidence_score,
                "feature_scores": {
                    "semantic_similarity": top_score.semantic_similarity if top_score else None,
                    "title_similarity": top_score.title_similarity if top_score else None,
                    "url_similarity": top_score.url_similarity if top_score else None,
                    "keyword_overlap": top_score.keyword_overlap if top_score else None,
                    "domain_score": top_score.domain_score if top_score else None,
                },
                "human_decision": decision,
                "reviewer": reviewer,
                "reviewer_comment": comment,
            }
            entries.append(entry)

            with open(FEEDBACK_DATASET_PATH, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
            logger.info(f"Recorded human review decision into {FEEDBACK_DATASET_PATH.name}")
        except Exception as e:
            logger.error(f"Failed to record feedback dataset entry: {e}")
