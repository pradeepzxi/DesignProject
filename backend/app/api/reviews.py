"""Human Review Queue API Routes."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.review import (
    ReviewQueueResponse,
    ReviewDecisionRequest,
)
from backend.app.services.review_service import HumanReviewService
from backend.app.repositories.review_repository import ReviewRepository

router = APIRouter(prefix="/reviews", tags=["Human Review Queue"])


@router.get("", response_model=List[ReviewQueueResponse])
def get_review_queue(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED, EDITED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve items from human review queue with document and candidate metadata."""
    service = HumanReviewService(db)
    items = service.get_review_items(status=status, skip=skip, limit=limit)
    return items


@router.get("/stats", response_model=Dict[str, int])
def get_review_stats(db: Session = Depends(get_db)):
    """Get counts of pending, approved, and rejected reviews."""
    repo = ReviewRepository(db)
    return {
        "pending": repo.count(status="PENDING"),
        "approved": repo.count(status="APPROVED"),
        "rejected": repo.count(status="REJECTED"),
        "total": repo.count(),
    }


@router.get("/{id}", response_model=ReviewQueueResponse)
def get_review_item(id: str, db: Session = Depends(get_db)):
    """Get a specific review item by review_id."""
    service = HumanReviewService(db)
    items = service.get_review_items(skip=0, limit=500)
    for it in items:
        if it.get("review_id") == id:
            return it
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review item {id} not found")


@router.post("/{id}/approve")
async def approve_candidate(
    id: str,
    reviewer: str = Query("HUMAN_OPERATOR", description="Reviewer name or identifier"),
    comment: Optional[str] = Query(None, description="Optional justification"),
    db: Session = Depends(get_db),
):
    """Approve candidate replacement: triggers autonomous document patching and records audit log."""
    service = HumanReviewService(db)
    try:
        result = await service.resolve_review(
            review_id=id,
            decision="APPROVE",
            reviewer=reviewer,
            comment=comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{id}/reject")
async def reject_candidate(
    id: str,
    reviewer: str = Query("HUMAN_OPERATOR", description="Reviewer name or identifier"),
    comment: Optional[str] = Query(None, description="Optional rejection reason"),
    db: Session = Depends(get_db),
):
    """Reject candidate replacement: logs decision and records negative sample in research feedback dataset."""
    service = HumanReviewService(db)
    try:
        result = await service.resolve_review(
            review_id=id,
            decision="REJECT",
            reviewer=reviewer,
            comment=comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{id}/decision")
async def submit_review_decision(
    id: str,
    req: ReviewDecisionRequest,
    db: Session = Depends(get_db),
):
    """Submit arbitrary review decision: APPROVE, REJECT, EDIT, or NO_REPLACEMENT."""
    service = HumanReviewService(db)
    try:
        result = await service.resolve_review(
            review_id=id,
            decision=req.decision,
            replacement_url=req.replacement_url,
            reviewer=req.reviewer,
            comment=req.comment,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
