"""Document Repository."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.scan_run import ScanRun


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.document_id == document_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        return (
            self.db.query(Document)
            .order_by(Document.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_total(self) -> int:
        return self.db.query(func.count(Document.document_id)).scalar() or 0

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_status(self, document_id: str, status: str, title: Optional[str] = None) -> Optional[Document]:
        doc = self.get_by_id(document_id)
        if doc:
            doc.processing_status = status
            if title:
                doc.document_title = title
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def delete(self, document_id: str) -> bool:
        doc = self.get_by_id(document_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False

    def get_document_stats(self, document_id: str) -> dict:
        """Get link summary statistics for a document."""
        total_links = (
            self.db.query(func.count(Link.link_id))
            .filter(Link.document_id == document_id)
            .scalar()
            or 0
        )
        valid_links = (
            self.db.query(func.count(Link.link_id))
            .filter(Link.document_id == document_id, Link.status == "VALID")
            .scalar()
            or 0
        )
        broken_links = (
            self.db.query(func.count(Link.link_id))
            .filter(
                Link.document_id == document_id,
                Link.status.in_(["BROKEN_404", "BROKEN_4XX", "SERVER_ERROR_5XX", "TIMEOUT", "DNS_ERROR", "CONNECTION_ERROR", "INVALID_URL"]),
            )
            .scalar()
            or 0
        )
        latest_scan = (
            self.db.query(ScanRun)
            .filter(ScanRun.document_id == document_id)
            .order_by(ScanRun.started_at.desc())
            .first()
        )

        return {
            "total_links": total_links,
            "valid_links": valid_links,
            "broken_links": broken_links,
            "last_scanned_at": latest_scan.started_at if latest_scan else None,
        }
