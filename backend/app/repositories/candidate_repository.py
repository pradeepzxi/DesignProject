"""Candidate and Scoring Repository."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from backend.app.models.prompt2_placeholders import Candidate, CandidateScore


class CandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        return (
            self.db.query(Candidate)
            .options(joinedload(Candidate.scores))
            .filter(Candidate.candidate_id == candidate_id)
            .first()
        )

    def get_candidates_by_link_id(self, link_id: str) -> List[Candidate]:
        return (
            self.db.query(Candidate)
            .options(joinedload(Candidate.scores))
            .filter(Candidate.link_id == link_id)
            .all()
        )

    def save_candidate_with_score(
        self,
        link_id: str,
        candidate_data: Dict[str, Any],
        score_data: Dict[str, Any],
    ) -> Candidate:
        candidate = Candidate(
            link_id=link_id,
            candidate_url=candidate_data["candidate_url"],
            title=candidate_data.get("title"),
            snippet=candidate_data.get("snippet"),
            content_text=candidate_data.get("content_text"),
            domain=candidate_data.get("domain"),
            source=candidate_data.get("source", "LOCAL_INTRANET"),
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)

        score = CandidateScore(
            candidate_id=candidate.candidate_id,
            semantic_similarity=score_data.get("semantic_similarity", 0.0),
            title_similarity=score_data.get("title_similarity", 0.0),
            url_similarity=score_data.get("url_similarity", 0.0),
            keyword_overlap=score_data.get("keyword_overlap", 0.0),
            domain_score=score_data.get("domain_score", 0.0),
            content_quality_score=score_data.get("content_quality_score", 0.0),
            overall_score=score_data.get("overall_score", 0.0),
            rank=score_data.get("rank", 1),
            explanation=score_data.get("explanation"),
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)

        return self.get_by_id(candidate.candidate_id)

    def clear_candidates_for_link(self, link_id: str):
        candidates = self.db.query(Candidate).filter(Candidate.link_id == link_id).all()
        for c in candidates:
            self.db.delete(c)
        self.db.commit()
