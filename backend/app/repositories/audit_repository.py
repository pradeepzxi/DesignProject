"""Audit Repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        action_type: str,
        document_id: Optional[str] = None,
        link_id: Optional[str] = None,
        old_url: Optional[str] = None,
        new_url: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        confidence_score: Optional[float] = None,
        actor: str = "SYSTEM",
    ) -> AuditLog:
        audit = AuditLog(
            action_type=action_type,
            document_id=document_id,
            link_id=link_id,
            old_url=old_url,
            new_url=new_url,
            status=status,
            reason=reason,
            confidence_score=confidence_score,
            actor=actor,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_recent_logs(self, limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_by_document(self, document_id: str, limit: int = 100) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.document_id == document_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
