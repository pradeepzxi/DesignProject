"""Recommendation Coordination Service.

Coordinates candidate discovery, feature extraction, hybrid ranking, confidence evaluation,
autonomous remediation execution, and human review triage.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.link import Link
from backend.app.repositories.link_repository import LinkRepository
from backend.app.repositories.candidate_repository import CandidateRepository
from backend.app.services.candidate_provider import default_candidate_provider
from backend.app.services.candidate_ranking_service import ranking_service
from backend.app.services.confidence_service import confidence_engine
from backend.app.services.remediation_service import AutonomousRemediationService
from backend.app.services.review_service import HumanReviewService
from backend.app.services.audit_service import AuditService
from backend.app.core.logging_config import logger


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.link_repo = LinkRepository(db)
        self.cand_repo = CandidateRepository(db)
        self.remediation_service = AutonomousRemediationService(db)
        self.review_service = HumanReviewService(db)

    async def generate_recommendation_for_link(
        self,
        link_id: str,
        auto_remediate: bool = True,
        custom_weights: Optional[Dict[str, float]] = None,
        disabled_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute candidate discovery, ranking, and routing for a broken hyperlink."""
        link = self.link_repo.get_by_id(link_id)
        if not link:
            raise ValueError(f"Link {link_id} not found")

        doc = link.document
        ctx = link.context

        context_dict = {
            "document_title": doc.document_title or doc.filename if doc else "",
            "section_heading": ctx.section_heading if ctx else "",
            "anchor_text": ctx.anchor_text if ctx else "",
            "surrounding_text": ctx.surrounding_text if ctx else "",
            "paragraph_text": ctx.paragraph_text if ctx else "",
            "keywords": ctx.keywords if ctx else [],
            "url_tokens": ctx.url_tokens if ctx else {},
        }

        # 1. Discover Candidates
        candidates = await default_candidate_provider.discover_candidates(
            broken_url=link.original_url,
            anchor_text=ctx.anchor_text if ctx else "",
            context=context_dict,
            max_candidates=5,
        )

        AuditService.log_event(
            db=self.db,
            action_type="CANDIDATES_FOUND",
            document_id=link.document_id,
            link_id=link.link_id,
            status="SUCCESS",
            reason=f"Discovered {len(candidates)} candidate replacements",
        )

        # 2. Rank Candidates
        ranked_candidates = await ranking_service.rank_candidates(
            broken_url=link.original_url,
            context=context_dict,
            candidates=candidates,
            custom_weights=custom_weights,
            disabled_features=disabled_features,
        )

        # Clear any prior candidates for clean state
        self.cand_repo.clear_candidates_for_link(link.link_id)

        # 3. Persist Candidates and Scores
        saved_candidates = []
        for c in ranked_candidates:
            saved_c = self.cand_repo.save_candidate_with_score(
                link_id=link.link_id,
                candidate_data={
                    "candidate_url": c["candidate_url"],
                    "title": c.get("title"),
                    "snippet": c.get("snippet"),
                    "content_text": c.get("content_text"),
                    "domain": c.get("domain"),
                    "source": c.get("source"),
                },
                score_data={
                    "semantic_similarity": c["features"].get("semantic_similarity", 0.0),
                    "title_similarity": c["features"].get("title_similarity", 0.0),
                    "url_similarity": c["features"].get("url_similarity", 0.0),
                    "keyword_overlap": c["features"].get("keyword_overlap", 0.0),
                    "domain_score": c["features"].get("domain_score", 0.0),
                    "content_quality_score": c["features"].get("content_quality_score", 0.0),
                    "overall_score": c["overall_score"],
                    "rank": c["rank"],
                    "explanation": c["explanation"],
                },
            )
            saved_candidates.append(saved_c)

            AuditService.log_event(
                db=self.db,
                action_type="CANDIDATE_RANKED",
                document_id=link.document_id,
                link_id=link.link_id,
                new_url=c["candidate_url"],
                confidence_score=c["overall_score"],
                status="RANKED",
                reason=f"Rank #{c['rank']} (Score: {round(c['overall_score'] * 100, 1)}%)",
            )

        top_cand = ranked_candidates[0] if ranked_candidates else None
        top_saved_c = saved_candidates[0] if saved_candidates else None

        # 4. Confidence Evaluation and Routing
        decision, confidence, decision_reason = confidence_engine.evaluate_candidate(
            broken_url=link.original_url,
            top_candidate=top_cand,
        )

        # 5. Routing Execution
        remediation_result = None
        if decision == "AUTO_REPAIR":
            AuditService.log_event(
                db=self.db,
                action_type="AUTO_REPAIR_SELECTED",
                document_id=link.document_id,
                link_id=link.link_id,
                new_url=top_cand["candidate_url"] if top_cand else None,
                confidence_score=confidence,
                status="AUTO_REPAIR",
                reason=decision_reason,
            )
            if auto_remediate and top_cand:
                remediation_result = await self.remediation_service.apply_remediation(
                    link_id=link.link_id,
                    replacement_url=top_cand["candidate_url"],
                    confidence_score=confidence,
                    actor="SYSTEM_AUTO_REMEDIATOR",
                    action="AUTO_REPAIRED",
                )
        elif decision == "HUMAN_REVIEW":
            self.review_service.submit_for_review(
                link_id=link.link_id,
                candidate_id=top_saved_c.candidate_id if top_saved_c else None,
                confidence_score=confidence,
            )

        return {
            "link_id": link.link_id,
            "broken_url": link.original_url,
            "failure_type": link.status,
            "anchor_text": ctx.anchor_text if ctx else None,
            "section_heading": ctx.section_heading if ctx else None,
            "document_title": doc.document_title if doc else None,
            "candidates": [
                {
                    "candidate_id": sc.candidate_id,
                    "candidate_url": sc.candidate_url,
                    "title": sc.title,
                    "snippet": sc.snippet,
                    "domain": sc.domain,
                    "source": sc.source,
                    "retrieved_at": sc.retrieved_at,
                    "score": {
                        "semantic_similarity": sc.scores[0].semantic_similarity if sc.scores else 0.0,
                        "title_similarity": sc.scores[0].title_similarity if sc.scores else 0.0,
                        "url_similarity": sc.scores[0].url_similarity if sc.scores else 0.0,
                        "keyword_overlap": sc.scores[0].keyword_overlap if sc.scores else 0.0,
                        "domain_score": sc.scores[0].domain_score if sc.scores else 0.0,
                        "content_quality_score": sc.scores[0].content_quality_score if sc.scores else 0.0,
                        "overall_score": sc.scores[0].overall_score if sc.scores else 0.0,
                        "rank": sc.scores[0].rank if sc.scores else 1,
                        "explanation": sc.scores[0].explanation if sc.scores else "",
                    } if sc.scores else None,
                }
                for sc in saved_candidates
            ],
            "top_candidate": {
                "candidate_url": top_cand["candidate_url"],
                "title": top_cand["title"],
                "overall_score": top_cand["overall_score"],
                "explanation": top_cand["explanation"],
            } if top_cand else None,
            "decision": decision,
            "confidence_score": confidence,
            "decision_reason": decision_reason,
            "remediation": remediation_result,
        }
