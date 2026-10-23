"""Document API Routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
)
from backend.app.schemas.scan_run import ScanRunResponse
from backend.app.schemas.link import LinkResponse
from backend.app.services.document_service import DocumentService
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.link_repository import LinkRepository
from backend.app.repositories.scan_repository import ScanRepository

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF or DOCX file, store it safely, and extract hyperlinks."""
    service = DocumentService(db)
    try:
        saved_doc = await service.ingest_document(file)
        # Compute link stats for response
        stats = service.doc_repo.get_document_stats(saved_doc.document_id)
        return DocumentResponse(
            document_id=saved_doc.document_id,
            filename=saved_doc.filename,
            file_type=saved_doc.file_type,
            file_size=saved_doc.file_size,
            upload_timestamp=saved_doc.upload_timestamp,
            version=saved_doc.version,
            processing_status=saved_doc.processing_status,
            document_title=saved_doc.document_title,
            storage_path=saved_doc.storage_path,
            links_count=stats["total_links"],
            valid_links_count=stats["valid_links"],
            broken_links_count=stats["broken_links"],
            last_scanned_at=stats["last_scanned_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}",
        )


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retrieve all uploaded documents with summary statistics."""
    repo = DocumentRepository(db)
    docs = repo.get_all(skip=skip, limit=limit)
    response_list = []
    for doc in docs:
        stats = repo.get_document_stats(doc.document_id)
        response_list.append(
            DocumentResponse(
                document_id=doc.document_id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                upload_timestamp=doc.upload_timestamp,
                version=doc.version,
                processing_status=doc.processing_status,
                document_title=doc.document_title,
                storage_path=doc.storage_path,
                links_count=stats["total_links"],
                valid_links_count=stats["valid_links"],
                broken_links_count=stats["broken_links"],
                last_scanned_at=stats["last_scanned_at"],
            )
        )
    return response_list


@router.get("/{id}", response_model=DocumentDetailResponse)
def get_document_by_id(
    id: str,
    db: Session = Depends(get_db),
):
    """Get single document details, associated links, and latest scan information."""
    doc_repo = DocumentRepository(db)
    link_repo = LinkRepository(db)
    scan_repo = ScanRepository(db)

    doc = doc_repo.get_by_id(id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

    stats = doc_repo.get_document_stats(id)
    links = link_repo.get_by_document_id(id)
    scans = scan_repo.get_by_document_id(id, limit=1)
    latest_scan = scans[0] if scans else None

    return DocumentDetailResponse(
        document_id=doc.document_id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_timestamp=doc.upload_timestamp,
        version=doc.version,
        processing_status=doc.processing_status,
        document_title=doc.document_title,
        storage_path=doc.storage_path,
        links_count=stats["total_links"],
        valid_links_count=stats["valid_links"],
        broken_links_count=stats["broken_links"],
        last_scanned_at=stats["last_scanned_at"],
        links=[
            LinkResponse(
                link_id=l.link_id,
                document_id=l.document_id,
                original_url=l.original_url,
                normalized_url=l.normalized_url,
                status=l.status,
                status_code=l.status_code,
                final_url=l.final_url,
                response_time_ms=l.response_time_ms,
                content_type=l.content_type,
                last_checked=l.last_checked,
                error_message=l.error_message,
                page_number=l.page_number,
                location_description=l.location_description,
                document_title=doc.document_title,
                document_filename=doc.filename,
            )
            for l in links
        ],
        latest_scan=(
            ScanRunResponse(
                scan_id=latest_scan.scan_id,
                document_id=latest_scan.document_id,
                started_at=latest_scan.started_at,
                completed_at=latest_scan.completed_at,
                total_links=latest_scan.total_links,
                valid_links=latest_scan.valid_links,
                broken_links=latest_scan.broken_links,
                redirected_links=latest_scan.redirected_links,
                failed_links=latest_scan.failed_links,
                scan_status=latest_scan.scan_status,
            )
            if latest_scan
            else None
        ),
    )


@router.post("/{id}/scan", response_model=ScanRunResponse)
async def scan_document_links(
    id: str,
    db: Session = Depends(get_db),
):
    """Trigger an asynchronous link integrity scan for all links in the document."""
    service = DocumentService(db)
    try:
        completed_scan = await service.run_document_scan(id)
        return ScanRunResponse(
            scan_id=completed_scan.scan_id,
            document_id=completed_scan.document_id,
            started_at=completed_scan.started_at,
            completed_at=completed_scan.completed_at,
            total_links=completed_scan.total_links,
            valid_links=completed_scan.valid_links,
            broken_links=completed_scan.broken_links,
            redirected_links=completed_scan.redirected_links,
            failed_links=completed_scan.failed_links,
            scan_status=completed_scan.scan_status,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scanning failed: {str(e)}",
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    id: str,
    db: Session = Depends(get_db),
):
    """Delete a document and its associated links."""
    repo = DocumentRepository(db)
    deleted = repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
