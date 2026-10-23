"""Remediations API Routes."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.remediation import RemediationResponse
from backend.app.repositories.remediation_repository import RemediationRepository

router = APIRouter(prefix="/remediations", tags=["Autonomous Remediations"])


@router.get("", response_model=List[RemediationResponse])
def get_remediations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve historical autonomous and manual link remediation actions."""
    repo = RemediationRepository(db)
    items = repo.get_all(skip=skip, limit=limit)
    res = []
    for it in items:
        doc = it.link.document if it.link else None
        res.append(
            RemediationResponse(
                remediation_id=it.remediation_id,
                link_id=it.link_id,
                old_url=it.old_url,
                new_url=it.new_url,
                confidence_score=it.confidence_score,
                action=it.action,
                validation_result=it.validation_result,
                created_at=it.created_at,
                completed_at=it.completed_at,
                actor=it.actor,
                status=it.status,
                document_id=doc.document_id if doc else None,
                document_filename=doc.filename if doc else None,
            )
        )
    return res


@router.get("/stats", response_model=Dict[str, Any])
def get_remediation_stats(db: Session = Depends(get_db)):
    """Retrieve aggregate remediation performance metrics (success rate, auto vs manual)."""
    repo = RemediationRepository(db)
    return repo.get_stats()


@router.get("/{id}", response_model=RemediationResponse)
def get_remediation_by_id(id: str, db: Session = Depends(get_db)):
    """Retrieve single remediation record by ID."""
    repo = RemediationRepository(db)
    it = repo.get_by_id(id)
    if not it:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Remediation {id} not found")
    doc = it.link.document if it.link else None
    return RemediationResponse(
        remediation_id=it.remediation_id,
        link_id=it.link_id,
        old_url=it.old_url,
        new_url=it.new_url,
        confidence_score=it.confidence_score,
        action=it.action,
        validation_result=it.validation_result,
        created_at=it.created_at,
        completed_at=it.completed_at,
        actor=it.actor,
        status=it.status,
        document_id=doc.document_id if doc else None,
        document_filename=doc.filename if doc else None,
    )
