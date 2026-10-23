"""Document Management Service.

Coordinates document ingestion, file system storage, parsing, link extraction,
and automated scanning orchestration.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.scan_run import ScanRun
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.link_repository import LinkRepository
from backend.app.repositories.scan_repository import ScanRepository
from backend.app.services.audit_service import AuditService
from backend.app.services.link_extraction_service import LinkExtractionService
from backend.app.services.link_validation_service import validation_service
from backend.app.utils.file_utils import sanitize_filename, validate_file_upload


def get_utc_now():
    return datetime.now(timezone.utc)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.link_repo = LinkRepository(db)
        self.scan_repo = ScanRepository(db)

    async def ingest_document(self, upload_file: UploadFile) -> Document:
        """Validate, persist to disk, and register document in the database."""
        raw_filename = upload_file.filename or "uploaded_file"
        clean_name = sanitize_filename(raw_filename)
        ext = Path(clean_name).suffix.lower()

        # Read file contents into memory to validate
        contents = await upload_file.read()
        file_size = len(contents)

        is_valid, reason = validate_file_upload(
            filename=clean_name,
            content_type=upload_file.content_type or "",
            file_size=file_size,
        )
        if not is_valid:
            raise ValueError(reason)

        # Unique storage path
        timestamp_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp_prefix}_{clean_name}"
        storage_filepath = settings.DOCUMENTS_DIR / safe_filename

        with open(storage_filepath, "wb") as f:
            f.write(contents)

        doc = Document(
            filename=clean_name,
            file_type=ext.strip("."),
            file_size=file_size,
            processing_status="PENDING",
            document_title=Path(clean_name).stem.replace("_", " ").title(),
            storage_path=str(storage_filepath),
        )
        saved_doc = self.doc_repo.create(doc)

        AuditService.log_event(
            db=self.db,
            action_type="DOCUMENT_UPLOADED",
            document_id=saved_doc.document_id,
            status="SUCCESS",
            reason=f"Uploaded {clean_name} ({file_size} bytes)",
            actor="USER",
        )

        # Auto-parse links after ingestion
        try:
            self.extract_and_store_links(saved_doc.document_id)
        except Exception as e:
            logger.error(f"Error during post-upload extraction for {saved_doc.document_id}: {e}")

        return saved_doc

    def extract_and_store_links(self, document_id: str) -> List[Link]:
        """Parse document and persist extracted hyperlinks with structural context."""
        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        doc_path = Path(doc.storage_path)
        if not doc_path.exists():
            raise FileNotFoundError(f"Stored file not found: {doc.storage_path}")

        doc_title, valid_links, malformed = LinkExtractionService.extract_links_from_file(
            file_path=doc_path,
            file_type=doc.file_type,
        )

        # Update document title if discovered from parsing
        self.doc_repo.update_status(document_id, status="PARSED", title=doc_title)

        created_links = []
        for item in valid_links:
            link = Link(
                document_id=document_id,
                original_url=item["original_url"],
                normalized_url=item["normalized_url"],
                status="PENDING",
                page_number=item.get("page_number"),
                location_description=item.get("location_description"),
            )
            saved_link = self.link_repo.create(link)

            ctx_data = item.get("context", {})
            link_context = LinkContext(
                link_id=saved_link.link_id,
                anchor_text=ctx_data.get("anchor_text"),
                surrounding_text=ctx_data.get("surrounding_text"),
                paragraph_text=ctx_data.get("paragraph_text"),
                section_heading=ctx_data.get("section_heading"),
                document_title=ctx_data.get("document_title"),
                url_tokens=ctx_data.get("url_tokens"),
                keywords=ctx_data.get("keywords"),
            )
            self.link_repo.create_context(link_context)

            AuditService.log_event(
                db=self.db,
                action_type="LINK_EXTRACTED",
                document_id=document_id,
                link_id=saved_link.link_id,
                old_url=saved_link.original_url,
                status="PENDING",
                reason=f"Extracted from {item.get('location_description')}",
            )
            created_links.append(saved_link)

        return created_links

    async def run_document_scan(self, document_id: str) -> ScanRun:
        """Scan and asynchronously validate all links extracted from a document."""
        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        links = self.link_repo.get_by_document_id(document_id)
        if not links:
            # Attempt extraction if links have not been extracted yet
            links = self.extract_and_store_links(document_id)

        # Create scan run record
        scan_run = ScanRun(
            document_id=document_id,
            scan_status="IN_PROGRESS",
            total_links=len(links),
        )
        saved_scan = self.scan_repo.create(scan_run)

        AuditService.log_event(
            db=self.db,
            action_type="SCAN_STARTED",
            document_id=document_id,
            status="IN_PROGRESS",
            reason=f"Initiated validation run for {len(links)} links",
        )

        self.doc_repo.update_status(document_id, status="SCANNING")

        valid_count = 0
        broken_count = 0
        redirect_count = 0
        failed_count = 0

        # Validate links concurrently with bounded concurrency
        validation_payloads = [
            {"original_url": l.original_url, "normalized_url": l.normalized_url}
            for l in links
        ]
        results = await validation_service.validate_batch(validation_payloads)

        for link, res in zip(links, results):
            status = res.status
            if status == "VALID":
                valid_count += 1
            elif status == "REDIRECT":
                redirect_count += 1
            elif status in [
                "BROKEN_404", "BROKEN_4XX", "SERVER_ERROR_5XX",
                "TIMEOUT", "DNS_ERROR", "CONNECTION_ERROR", "INVALID_URL",
                "FORBIDDEN", "UNAUTHORIZED"
            ]:
                broken_count += 1
            else:
                failed_count += 1

            self.link_repo.update_validation(
                link_id=link.link_id,
                status=status,
                status_code=res.status_code,
                final_url=res.final_url,
                response_time_ms=res.response_time_ms,
                content_type=res.content_type,
                error_message=res.error_message,
                last_checked=res.validation_timestamp,
            )

            # Audit event per link
            AuditService.log_event(
                db=self.db,
                action_type="LINK_VALIDATED",
                document_id=document_id,
                link_id=link.link_id,
                old_url=link.original_url,
                new_url=res.final_url if res.final_url != link.original_url else None,
                status=status,
                reason=res.error_message or f"HTTP {res.status_code}",
            )

            if status in ["BROKEN_404", "BROKEN_4XX", "SERVER_ERROR_5XX", "TIMEOUT", "DNS_ERROR", "CONNECTION_ERROR"]:
                AuditService.log_event(
                    db=self.db,
                    action_type="LINK_BROKEN",
                    document_id=document_id,
                    link_id=link.link_id,
                    old_url=link.original_url,
                    status=status,
                    reason=res.error_message or f"HTTP status {res.status_code}",
                )
            elif status == "REDIRECT":
                AuditService.log_event(
                    db=self.db,
                    action_type="LINK_REDIRECTED",
                    document_id=document_id,
                    link_id=link.link_id,
                    old_url=link.original_url,
                    new_url=res.final_url,
                    status="REDIRECT",
                    reason=f"Redirected ({res.redirect_count} hops)",
                )

        completed_scan = self.scan_repo.update_completion(
            scan_id=saved_scan.scan_id,
            total_links=len(links),
            valid_links=valid_count,
            broken_links=broken_count,
            redirected_links=redirect_count,
            failed_links=failed_count,
            status="COMPLETED",
            completed_at=get_utc_now(),
        )

        self.doc_repo.update_status(document_id, status="COMPLETED")

        AuditService.log_event(
            db=self.db,
            action_type="SCAN_COMPLETED",
            document_id=document_id,
            status="COMPLETED",
            reason=f"Scan finished: {valid_count} valid, {broken_count} broken, {redirect_count} redirected",
        )

        return completed_scan
