"""Audit Log API Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.audit_log import AuditLogResponse
from backend.app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    document_id: Optional[str] = Query(None, description="Filter logs by Document ID"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve chronologically ordered audit trail events for system telemetry."""
    repo = AuditRepository(db)
    if document_id:
        logs = repo.get_by_document(document_id, limit=limit)
    else:
        logs = repo.get_recent_logs(limit=limit)

    return [
        AuditLogResponse(
            audit_id=l.audit_id,
            timestamp=l.timestamp,
            document_id=l.document_id,
            link_id=l.link_id,
            action_type=l.action_type,
            old_url=l.old_url,
            new_url=l.new_url,
            status=l.status,
            reason=l.reason,
            confidence_score=l.confidence_score,
            actor=l.actor,
        )
        for l in logs
    ]
