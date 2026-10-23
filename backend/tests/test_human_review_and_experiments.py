"""Tests for Human Review Queue, Feedback persistence, and Experiment Pipeline."""

import pytest
from backend.app.services.review_service import HumanReviewService
from backend.app.services.experiment_service import BenchmarkExperimentService
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.prompt2_placeholders import ReviewQueueItem


@pytest.mark.asyncio
async def test_human_review_triage_flow(db_session, tmp_path):
    # Setup document and link
    doc_path = tmp_path / "test_doc.docx"
    doc_path.write_text("sample")

    db_doc = Document(filename="test_doc.docx", storage_path=str(doc_path), file_type="docx", file_size=1024)
    db_session.add(db_doc)
    db_session.commit()

    db_link = Link(
        document_id=db_doc.document_id,
        original_url="https://broken.corp/tool",
        normalized_url="https://broken.corp/tool",
        status="BROKEN_404",
    )
    db_session.add(db_link)
    db_session.commit()

    service = HumanReviewService(db_session)

    # 1. Enqueue
    item = service.submit_for_review(link_id=db_link.link_id, candidate_id=None, confidence_score=0.78)
    assert item.review_status == "PENDING"
    assert item.confidence_score == 0.78

    # 2. Reject
    res_reject = await service.resolve_review(
        review_id=item.review_id,
        decision="REJECT",
        reviewer="HUMAN_OPERATOR",
        comment="Incorrect candidate domain",
    )
    assert res_reject["success"] is True
    assert res_reject["decision"] == "REJECT"

    # Verify status in DB
    refreshed = service.review_repo.get_by_id(item.review_id)
    assert refreshed.review_status in ("REJECT", "REJECTED")
    assert refreshed.reviewer == "HUMAN_OPERATOR"


@pytest.mark.asyncio
async def test_benchmark_experiment_execution():
    results = await BenchmarkExperimentService.run_experiment(method="BASELINE_URL")

    assert "retrieval_metrics" in results
    assert "remediation_metrics" in results
    assert "detection_metrics" in results
    assert results["total_test_cases"] == 60
    assert 0.0 <= results["retrieval_metrics"]["top1_accuracy"] <= 1.0
    assert 0.0 <= results["retrieval_metrics"]["mrr"] <= 1.0
    assert results["efficiency"]["avg_case_latency_ms"] > 0.0
