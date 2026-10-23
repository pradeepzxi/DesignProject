"""Scan Run Repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.scan_run import ScanRun


class ScanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, scan_id: str) -> Optional[ScanRun]:
        return self.db.query(ScanRun).filter(ScanRun.scan_id == scan_id).first()

    def get_by_document_id(self, document_id: str, limit: int = 20) -> List[ScanRun]:
        return (
            self.db.query(ScanRun)
            .filter(ScanRun.document_id == document_id)
            .order_by(ScanRun.started_at.desc())
            .limit(limit)
            .all()
        )

    def create(self, scan_run: ScanRun) -> ScanRun:
        self.db.add(scan_run)
        self.db.commit()
        self.db.refresh(scan_run)
        return scan_run

    def update_completion(
        self,
        scan_id: str,
        total_links: int,
        valid_links: int,
        broken_links: int,
        redirected_links: int,
        failed_links: int,
        status: str,
        completed_at,
    ) -> Optional[ScanRun]:
        scan = self.get_by_id(scan_id)
        if scan:
            scan.total_links = total_links
            scan.valid_links = valid_links
            scan.broken_links = broken_links
            scan.redirected_links = redirected_links
            scan.failed_links = failed_links
            scan.scan_status = status
            scan.completed_at = completed_at
            self.db.commit()
            self.db.refresh(scan)
        return scan

    def count_total_scans(self) -> int:
        return self.db.query(func.count(ScanRun.scan_id)).scalar() or 0
