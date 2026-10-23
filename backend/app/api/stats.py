"""Statistics and Dashboard API Routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.stats import DashboardOverviewResponse, DistributionItem

router = APIRouter(prefix="/stats", tags=["Statistics"])

COLOR_MAP = {
    "VALID": "#10B981",  # Emerald Green
    "REDIRECT": "#3B82F6",  # Blue
    "BROKEN_404": "#EF4444",  # Red
    "BROKEN_4XX": "#F97316",  # Orange
    "SERVER_ERROR_5XX": "#DC2626",  # Dark Red
    "TIMEOUT": "#F59E0B",  # Amber
    "DNS_ERROR": "#8B5CF6",  # Violet
    "CONNECTION_ERROR": "#EC4899",  # Pink
    "FORBIDDEN": "#6366F1",  # Indigo
    "UNAUTHORIZED": "#A855F7",  # Purple
    "INVALID_URL": "#64748B",  # Slate
    "PENDING": "#94A3B8",  # Gray
    "UNKNOWN": "#6B7280",  # Gray
}


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(db: Session = Depends(get_db)):
    """Fetch aggregated system telemetry, health distributions, and recent audit activity."""
    total_docs = db.query(func.count(Document.document_id)).scalar() or 0
    scanned_docs = (
        db.query(func.count(Document.document_id))
        .filter(Document.processing_status == "COMPLETED")
        .scalar()
        or 0
    )

    total_links = db.query(func.count(Link.link_id)).scalar() or 0
    valid_links = (
        db.query(func.count(Link.link_id))
        .filter(Link.status == "VALID")
        .scalar()
        or 0
    )
    redirected_links = (
        db.query(func.count(Link.link_id))
        .filter(Link.status == "REDIRECT")
        .scalar()
        or 0
    )
    pending_links = (
        db.query(func.count(Link.link_id))
        .filter(Link.status == "PENDING")
        .scalar()
        or 0
    )

    broken_statuses = [
        "BROKEN_404", "BROKEN_4XX", "SERVER_ERROR_5XX",
        "TIMEOUT", "DNS_ERROR", "CONNECTION_ERROR", "INVALID_URL",
        "FORBIDDEN", "UNAUTHORIZED"
    ]
    broken_links = (
        db.query(func.count(Link.link_id))
        .filter(Link.status.in_(broken_statuses))
        .scalar()
        or 0
    )

    failed_links = (
        db.query(func.count(Link.link_id))
        .filter(Link.status.in_(["UNKNOWN", "CONNECTION_ERROR", "DNS_ERROR", "TIMEOUT"]))
        .scalar()
        or 0
    )

    # Status distribution breakdown
    status_counts = (
        db.query(Link.status, func.count(Link.link_id))
        .group_by(Link.status)
        .all()
    )

    status_dist = []
    for st, count in status_counts:
        pct = round((count / total_links * 100), 1) if total_links > 0 else 0.0
        status_dist.append(
            DistributionItem(
                name=st.replace("_", " ").title(),
                value=count,
                percentage=pct,
                color=COLOR_MAP.get(st, "#6B7280"),
            )
        )

    # Failure-type breakdown for broken links
    failure_counts = (
        db.query(Link.status, func.count(Link.link_id))
        .filter(Link.status.in_(broken_statuses))
        .group_by(Link.status)
        .all()
    )

    failure_dist = []
    for st, count in failure_counts:
        pct = round((count / broken_links * 100), 1) if broken_links > 0 else 0.0
        failure_dist.append(
            DistributionItem(
                name=st.replace("_", " ").title(),
                value=count,
                percentage=pct,
                color=COLOR_MAP.get(st, "#EF4444"),
            )
        )

    # Recent activity stream
    recent_audits = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )

    recent_activity = [
        {
            "id": a.audit_id,
            "timestamp": a.timestamp.isoformat(),
            "action_type": a.action_type,
            "document_id": a.document_id,
            "link_id": a.link_id,
            "status": a.status,
            "reason": a.reason,
            "actor": a.actor,
        }
        for a in recent_audits
    ]

    return DashboardOverviewResponse(
        total_documents=total_docs,
        scanned_documents=scanned_docs,
        total_links=total_links,
        valid_links=valid_links,
        broken_links=broken_links,
        redirected_links=redirected_links,
        failed_links=failed_links,
        pending_links=pending_links,
        status_distribution=status_dist,
        failure_distribution=failure_dist,
        recent_activity=recent_activity,
    )
