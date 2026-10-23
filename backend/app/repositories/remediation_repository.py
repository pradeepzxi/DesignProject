"""Remediation Repository."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, timezone
from backend.app.models.prompt2_placeholders import Remediation
from backend.app.models.link import Link
from backend.app.models.document import Document


def get_utc_now():
    return datetime.now(timezone.utc)


class RemediationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, remediation_id: str) -> Optional[Remediation]:
        return (
            self.db.query(Remediation)
            .options(joinedload(Remediation.link))
            .filter(Remediation.remediation_id == remediation_id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Remediation]:
        return (
            self.db.query(Remediation)
            .options(joinedload(Remediation.link).joinedload(Link.document))
            .order_by(Remediation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        link_id: str,
        old_url: str,
        new_url: str,
        confidence_score: float,
        action: str,
        validation_result: str = "VERIFIED_WORKING",
        actor: str = "SYSTEM",
        status: str = "COMPLETED",
    ) -> Remediation:
        rem = Remediation(
            link_id=link_id,
            old_url=old_url,
            new_url=new_url,
            confidence_score=confidence_score,
            action=action,
            validation_result=validation_result,
            actor=actor,
            status=status,
            completed_at=get_utc_now(),
        )
        self.db.add(rem)
        self.db.commit()
        self.db.refresh(rem)
        return rem

    def count_total(self) -> int:
        return self.db.query(func.count(Remediation.remediation_id)).scalar() or 0

    def get_stats(self) -> Dict[str, Any]:
        total = self.count_total()
        auto_count = (
            self.db.query(func.count(Remediation.remediation_id))
            .filter(Remediation.action == "AUTO_REPAIRED")
            .scalar()
            or 0
        )
        manual_count = (
            self.db.query(func.count(Remediation.remediation_id))
            .filter(Remediation.action == "MANUAL_APPROVED")
            .scalar()
            or 0
        )
        verified_count = (
            self.db.query(func.count(Remediation.remediation_id))
            .filter(Remediation.validation_result == "VERIFIED_WORKING")
            .scalar()
            or 0
        )
        failed_count = (
            self.db.query(func.count(Remediation.remediation_id))
            .filter(Remediation.validation_result == "FAILED")
            .scalar()
            or 0
        )

        return {
            "total_remediations": total,
            "auto_repaired": auto_count,
            "manual_approved": manual_count,
            "verified_working": verified_count,
            "failed_remediations": failed_count,
            "success_rate": round((verified_count / total * 100), 1) if total > 0 else 100.0,
        }
