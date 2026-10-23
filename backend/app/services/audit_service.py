"""Audit Service.

Maintains immutable logs for research traceability, verification, and auditability.
"""

from typing import Optional
from sqlalchemy.orm import Session
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.core.logging_config import logger


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action_type: str,
        document_id: Optional[str] = None,
        link_id: Optional[str] = None,
        old_url: Optional[str] = None,
        new_url: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        confidence_score: Optional[float] = None,
        actor: str = "SYSTEM",
    ):
        """Record an audit trail event in the database."""
        try:
            repo = AuditRepository(db)
            audit = repo.log_event(
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
            logger.info(
                f"[AUDIT] {action_type} | Doc: {document_id or '-'} | Link: {link_id or '-'} | Status: {status or '-'}"
            )
            return audit
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}", exc_info=True)
            return None
