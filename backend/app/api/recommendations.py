"""Recommendations and Autonomous Remediation API Routes."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.candidate import (
    CandidateResponse,
    RecommendationResponse,
)
from backend.app.schemas.remediation import (
    RemediationResponse,
    RemediationRequest,
)
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.remediation_service import AutonomousRemediationService
from backend.app.repositories.candidate_repository import CandidateRepository
from backend.app.repositories.link_repository import LinkRepository

router = APIRouter(prefix="/links", tags=["Recommendations & Remediation"])


@router.post("/{id}/discover-candidates", response_model=RecommendationResponse)
async def discover_and_rank_candidates(
    id: str,
    auto_remediate: bool = Query(False, description="Automatically apply high-confidence repairs immediately"),
    db: Session = Depends(get_db),
):
    """Discover, feature-extract, rank, and evaluate replacement candidates for a link."""
    service = RecommendationService(db)
    try:
        rec = await service.generate_recommendation_for_link(
            link_id=id,
            auto_remediate=auto_remediate,
        )
        return rec
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Recommendation failed: {str(e)}")


@router.get("/{id}/candidates", response_model=List[CandidateResponse])
def get_link_candidates(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all ranked candidates and multi-factor scores previously discovered for a link."""
    repo = CandidateRepository(db)
    candidates = repo.get_candidates_by_link_id(id)
    result = []
    for c in candidates:
        top_score = c.scores[0] if c.scores else None
        result.append(
            CandidateResponse(
                candidate_id=c.candidate_id,
                link_id=c.link_id,
                candidate_url=c.candidate_url,
                title=c.title,
                snippet=c.snippet,
                content_text=c.content_text,
                domain=c.domain,
                source=c.source,
                retrieved_at=c.retrieved_at,
                score=top_score,
            )
        )
    return result


@router.post("/{id}/recommend", response_model=RecommendationResponse)
async def recommend_link_replacement(
    id: str,
    auto_remediate: bool = Query(True, description="Automatically execute remediation for scores >= 0.90"),
    db: Session = Depends(get_db),
):
    """Full pipeline recommendation: discover, multi-factor rank, score confidence, and route."""
    service = RecommendationService(db)
    try:
        return await service.generate_recommendation_for_link(
            link_id=id,
            auto_remediate=auto_remediate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{id}/repair", response_model=Dict[str, Any])
async def repair_hyperlink(
    id: str,
    req: RemediationRequest,
    db: Session = Depends(get_db),
):
    """Directly trigger document backup, hyperlink replacement, and post-repair verification."""
    service = AutonomousRemediationService(db)
    cand_repo = CandidateRepository(db)
    link_repo = LinkRepository(db)

    link = link_repo.get_by_id(id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    target_url = req.candidate_url
    confidence = 1.0

    if not target_url:
        candidates = cand_repo.get_candidates_by_link_id(id)
        if not candidates:
            # Generate recommendation on the fly
            rec_service = RecommendationService(db)
            rec = await rec_service.generate_recommendation_for_link(id, auto_remediate=False)
            if not rec.get("top_candidate"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No suitable candidate found to repair link")
            target_url = rec["top_candidate"]["candidate_url"]
            confidence = rec["top_candidate"]["overall_score"]
        else:
            target_url = candidates[0].candidate_url
            confidence = candidates[0].scores[0].overall_score if candidates[0].scores else 1.0

    result = await service.apply_remediation(
        link_id=id,
        replacement_url=target_url,
        confidence_score=confidence,
        actor=req.reviewer,
        action="MANUAL_APPROVED" if req.reviewer != "SYSTEM" else "AUTO_REPAIRED",
        dry_run=req.dry_run,
    )

    return result
