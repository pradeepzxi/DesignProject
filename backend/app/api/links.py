"""Link API Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.link import (
    LinkResponse,
    LinkDetailResponse,
)
from backend.app.schemas.link_context import LinkContextResponse
from backend.app.repositories.link_repository import LinkRepository
from backend.app.services.link_validation_service import validation_service
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/links", tags=["Links"])


@router.get("", response_model=List[LinkResponse])
def get_links(
    document_id: Optional[str] = Query(None, description="Filter by Document ID"),
    status: Optional[str] = Query(None, description="Filter by Link Status"),
    broken_only: bool = Query(False, description="Filter only broken and failure states"),
    search: Optional[str] = Query(None, description="Search by URL or location"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List links with flexible filtering for broken states, status, document, or search term."""
    repo = LinkRepository(db)
    links, _ = repo.get_all(
        document_id=document_id,
        status=status,
        broken_only=broken_only,
        search_query=search,
        skip=skip,
        limit=limit,
    )

    return [
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
            document_title=l.document.document_title if l.document else None,
            document_filename=l.document.filename if l.document else None,
        )
        for l in links
    ]


@router.get("/{id}", response_model=LinkDetailResponse)
def get_link_by_id(
    id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full details for a link including its linguistic, structural, and URL context."""
    repo = LinkRepository(db)
    link = repo.get_by_id(id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link {id} not found")

    context_resp = None
    if link.context:
        context_resp = LinkContextResponse(
            context_id=link.context.context_id,
            link_id=link.context.link_id,
            anchor_text=link.context.anchor_text,
            surrounding_text=link.context.surrounding_text,
            paragraph_text=link.context.paragraph_text,
            section_heading=link.context.section_heading,
            document_title=link.context.document_title,
            url_tokens=link.context.url_tokens,
            keywords=link.context.keywords,
        )

    return LinkDetailResponse(
        link_id=link.link_id,
        document_id=link.document_id,
        original_url=link.original_url,
        normalized_url=link.normalized_url,
        status=link.status,
        status_code=link.status_code,
        final_url=link.final_url,
        response_time_ms=link.response_time_ms,
        content_type=link.content_type,
        last_checked=link.last_checked,
        error_message=link.error_message,
        page_number=link.page_number,
        location_description=link.location_description,
        document_title=link.document.document_title if link.document else None,
        document_filename=link.document.filename if link.document else None,
        context=context_resp,
    )


@router.post("/{id}/validate", response_model=LinkDetailResponse)
async def revalidate_link(
    id: str,
    db: Session = Depends(get_db),
):
    """Re-validate an individual link directly."""
    repo = LinkRepository(db)
    link = repo.get_by_id(id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Link {id} not found")

    res = await validation_service.validate_url(
        url=link.original_url,
        normalized_url=link.normalized_url,
        use_cache=False,  # Force fresh validation
    )

    updated_link = repo.update_validation(
        link_id=link.link_id,
        status=res.status,
        status_code=res.status_code,
        final_url=res.final_url,
        response_time_ms=res.response_time_ms,
        content_type=res.content_type,
        error_message=res.error_message,
        last_checked=res.validation_timestamp,
    )

    AuditService.log_event(
        db=db,
        action_type="LINK_VALIDATED",
        document_id=link.document_id,
        link_id=link.link_id,
        old_url=link.original_url,
        new_url=res.final_url,
        status=res.status,
        reason=f"Manual revalidation: HTTP {res.status_code}",
        actor="USER",
    )

    return get_link_by_id(id, db)
