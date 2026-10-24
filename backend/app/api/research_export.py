"""Research Data Export API Routes.

Generates full scientific export in JSON and CSV formats for:
- Documents & Link Inventory
- Broken Links & Failure Classifications
- Candidate Recommendations & Feature Scores
- Remediation Audit Log & Verification Statuses
- Human Review Decisions
- Benchmark Experiment Results & Scientific Metrics
"""

import csv
import io
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.audit_log import AuditLog
from backend.app.models.prompt2_placeholders import (
    Candidate,
    CandidateScore,
    Remediation,
    ReviewQueueItem,
    ExperimentRun,
)
from backend.app.repositories.experiment_repository import ExperimentRepository

router = APIRouter(prefix="/research", tags=["Research Data & Publication Exports"])


@router.get("/summary")
def get_research_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Calculate and return live scientific research summary metrics from experimental data."""
    doc_count = db.query(func.count(Document.document_id)).scalar() or 0
    link_count = db.query(func.count(Link.link_id)).scalar() or 0
    broken_count = (
        db.query(func.count(Link.link_id))
        .filter(Link.status.in_(["BROKEN_404", "TIMEOUT", "DNS_ERROR", "AUTH_REQUIRED", "REDIRECT_301", "REDIRECT_302"]))
        .scalar()
        or 0
    )
    candidates_count = db.query(func.count(Candidate.candidate_id)).scalar() or 0
    remediations_count = db.query(func.count(Remediation.remediation_id)).scalar() or 0
    reviews_count = db.query(func.count(ReviewQueueItem.review_id)).scalar() or 0

    # Retrieve most recent Proposed Hybrid experiment run
    exp_repo = ExperimentRepository(db)
    latest_exp = (
        db.query(ExperimentRun)
        .filter(ExperimentRun.status == "COMPLETED")
        .order_by(ExperimentRun.completed_at.desc())
        .first()
    )

    exp_res = latest_exp.results if (latest_exp and latest_exp.results) else {}
    retrieval = exp_res.get("retrieval_metrics", {})
    remediation = exp_res.get("remediation_metrics", {})
    detection = exp_res.get("detection_metrics", {})

    return {
        "dataset_statistics": {
            "documents": doc_count,
            "links": link_count,
            "broken_links": broken_count,
            "candidates_evaluated": candidates_count,
            "remediations_executed": remediations_count,
            "human_reviews_logged": reviews_count,
        },
        "scientific_metrics": {
            "detection_precision": detection.get("precision"),
            "detection_recall": detection.get("recall"),
            "detection_f1": detection.get("f1"),
            "top1_accuracy": retrieval.get("top1_accuracy"),
            "top3_accuracy": retrieval.get("top3_accuracy"),
            "mrr": retrieval.get("mrr"),
            "automatic_repair_precision": remediation.get("auto_repair_precision"),
            "automatic_repair_rate": remediation.get("auto_repair_rate"),
            "false_repair_rate": remediation.get("false_repair_rate"),
            "human_review_rate": remediation.get("human_review_rate"),
        } if latest_exp else None,
        "latest_experiment_id": latest_exp.experiment_id if latest_exp else None,
        "latest_experiment_name": latest_exp.experiment_name if latest_exp else "None",
    }


@router.get("/export")
def export_research_data(
    format: str = Query("json", description="Export format: json or csv"),
    dataset_type: str = Query(
        "all",
        description="Dataset type: all, links, candidates, remediations, reviews, experiments",
    ),
    db: Session = Depends(get_db),
):
    """Export complete research dataset in JSON or CSV for scientific papers and replication."""
    if format.lower() == "csv":
        return _export_as_csv(db, dataset_type)
    else:
        return _export_as_json(db, dataset_type)


def _export_as_json(db: Session, dataset_type: str) -> Dict[str, Any]:
    summary = get_research_summary(db)

    data = {
        "metadata": {
            "title": "Intelligent Link Integrity Management and Autonomous Remediation Framework",
            "export_type": dataset_type,
            "summary": summary,
        }
    }

    if dataset_type in ("all", "links"):
        links = db.query(Link).all()
        data["links"] = [
            {
                "link_id": l.link_id,
                "document_id": l.document_id,
                "original_url": l.original_url,
                "normalized_url": l.normalized_url,
                "status": l.status,
                "http_status_code": l.http_status_code,
                "content_type": l.content_type,
                "error_message": l.error_message,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in links
        ]

    if dataset_type in ("all", "candidates"):
        candidates = db.query(Candidate).all()
        cand_list = []
        for c in candidates:
            score = c.scores[0] if c.scores else None
            cand_list.append({
                "candidate_id": c.candidate_id,
                "link_id": c.link_id,
                "candidate_url": c.candidate_url,
                "title": c.title,
                "domain": c.domain,
                "source": c.source,
                "semantic_similarity": score.semantic_similarity if score else None,
                "title_similarity": score.title_similarity if score else None,
                "url_similarity": score.url_similarity if score else None,
                "keyword_overlap": score.keyword_overlap if score else None,
                "domain_score": score.domain_score if score else None,
                "overall_score": score.overall_score if score else None,
                "rank": score.rank if score else None,
                "explanation": score.explanation if score else None,
            })
        data["candidates"] = cand_list

    if dataset_type in ("all", "remediations"):
        remediations = db.query(Remediation).all()
        data["remediations"] = [
            {
                "remediation_id": r.remediation_id,
                "link_id": r.link_id,
                "old_url": r.old_url,
                "new_url": r.new_url,
                "confidence_score": r.confidence_score,
                "action": r.action,
                "validation_result": r.validation_result,
                "actor": r.actor,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in remediations
        ]

    if dataset_type in ("all", "reviews"):
        reviews = db.query(ReviewQueueItem).all()
        data["reviews"] = [
            {
                "review_id": rv.review_id,
                "link_id": rv.link_id,
                "candidate_id": rv.candidate_id,
                "confidence_score": rv.confidence_score,
                "review_status": rv.review_status,
                "reviewer": rv.reviewer,
                "reviewer_comment": rv.reviewer_comment,
                "created_at": rv.created_at.isoformat() if rv.created_at else None,
                "reviewed_at": rv.reviewed_at.isoformat() if rv.reviewed_at else None,
            }
            for rv in reviews
        ]

    if dataset_type in ("all", "experiments"):
        experiments = db.query(ExperimentRun).all()
        data["experiments"] = [
            {
                "experiment_id": exp.experiment_id,
                "experiment_name": exp.experiment_name,
                "configuration": exp.configuration,
                "dataset_version": exp.dataset_version,
                "status": exp.status,
                "started_at": exp.started_at.isoformat() if exp.started_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "results": exp.results,
            }
            for exp in experiments
        ]

    return data


def _export_as_csv(db: Session, dataset_type: str) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)

    if dataset_type == "candidates":
        writer.writerow([
            "candidate_id", "link_id", "candidate_url", "title", "domain",
            "semantic_similarity", "title_similarity", "url_similarity",
            "keyword_overlap", "domain_score", "overall_score", "rank", "explanation"
        ])
        candidates = db.query(Candidate).all()
        for c in candidates:
            s = c.scores[0] if c.scores else None
            writer.writerow([
                c.candidate_id, c.link_id, c.candidate_url, c.title, c.domain,
                s.semantic_similarity if s else "",
                s.title_similarity if s else "",
                s.url_similarity if s else "",
                s.keyword_overlap if s else "",
                s.domain_score if s else "",
                s.overall_score if s else "",
                s.rank if s else "",
                s.explanation if s else "",
            ])
    elif dataset_type == "remediations":
        writer.writerow([
            "remediation_id", "link_id", "old_url", "new_url",
            "confidence_score", "action", "validation_result", "actor", "status", "created_at"
        ])
        remediations = db.query(Remediation).all()
        for r in remediations:
            writer.writerow([
                r.remediation_id, r.link_id, r.old_url, r.new_url,
                r.confidence_score, r.action, r.validation_result, r.actor, r.status,
                r.created_at.isoformat() if r.created_at else "",
            ])
    else:  # Default to links
        writer.writerow([
            "link_id", "document_id", "original_url", "status",
            "http_status_code", "content_type", "error_message", "created_at"
        ])
        links = db.query(Link).all()
        for l in links:
            writer.writerow([
                l.link_id, l.document_id, l.original_url, l.status,
                l.http_status_code, l.content_type, l.error_message,
                l.created_at.isoformat() if l.created_at else "",
            ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=research_export_{dataset_type}.csv"},
    )
