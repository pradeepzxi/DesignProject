"""Link Repository."""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.document import Document

BROKEN_STATUSES = [
    "BROKEN_404",
    "BROKEN_4XX",
    "SERVER_ERROR_5XX",
    "TIMEOUT",
    "DNS_ERROR",
    "CONNECTION_ERROR",
    "FORBIDDEN",
    "UNAUTHORIZED",
    "INVALID_URL",
]


class LinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, link_id: str) -> Optional[Link]:
        return (
            self.db.query(Link)
            .options(joinedload(Link.context), joinedload(Link.document))
            .filter(Link.link_id == link_id)
            .first()
        )

    def get_all(
        self,
        document_id: Optional[str] = None,
        status: Optional[str] = None,
        broken_only: bool = False,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Link], int]:
        query = self.db.query(Link).options(joinedload(Link.context), joinedload(Link.document))

        if document_id:
            query = query.filter(Link.document_id == document_id)

        if status:
            query = query.filter(Link.status == status)
        elif broken_only:
            query = query.filter(Link.status.in_(BROKEN_STATUSES))

        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter(
                (Link.original_url.ilike(pattern))
                | (Link.normalized_url.ilike(pattern))
                | (Link.location_description.ilike(pattern))
            )

        total = query.count()
        links = query.order_by(Link.last_checked.desc().nullslast()).offset(skip).limit(limit).all()
        return links, total

    def get_by_document_id(self, document_id: str) -> List[Link]:
        return (
            self.db.query(Link)
            .options(joinedload(Link.context))
            .filter(Link.document_id == document_id)
            .all()
        )

    def create(self, link: Link) -> Link:
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def bulk_create(self, links: List[Link]) -> List[Link]:
        self.db.add_all(links)
        self.db.commit()
        for link in links:
            self.db.refresh(link)
        return links

    def create_context(self, context: LinkContext) -> LinkContext:
        self.db.add(context)
        self.db.commit()
        self.db.refresh(context)
        return context

    def bulk_create_contexts(self, contexts: List[LinkContext]) -> List[LinkContext]:
        self.db.add_all(contexts)
        self.db.commit()
        return contexts

    def update_validation(
        self,
        link_id: str,
        status: str,
        status_code: Optional[int],
        final_url: Optional[str],
        response_time_ms: Optional[float],
        content_type: Optional[str],
        error_message: Optional[str],
        last_checked: Any,
    ) -> Optional[Link]:
        link = self.db.query(Link).filter(Link.link_id == link_id).first()
        if link:
            link.status = status
            link.status_code = status_code
            link.final_url = final_url
            link.response_time_ms = response_time_ms
            link.content_type = content_type
            link.error_message = error_message
            link.last_checked = last_checked
            self.db.commit()
            self.db.refresh(link)
        return link

    def get_status_counts(self) -> Dict[str, int]:
        results = (
            self.db.query(Link.status, func.count(Link.link_id))
            .group_by(Link.status)
            .all()
        )
        return {status: count for status, count in results}

    def get_links_by_normalized_url(self, normalized_url: str) -> List[Link]:
        """Find recent validations for caching reuse across documents."""
        return (
            self.db.query(Link)
            .filter(
                Link.normalized_url == normalized_url,
                Link.last_checked.isnot(None),
            )
            .order_by(Link.last_checked.desc())
            .all()
        )
