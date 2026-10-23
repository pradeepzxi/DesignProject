"""End-to-End Integration Test.

Validates the complete research pipeline:
Upload Document -> Parse File -> Extract Hyperlinks -> Validate URLs -> Persist & Query Results
"""

import io
from pathlib import Path
import pymupdf
import pytest
from backend.app.schemas.link import LinkValidationResult


def create_sample_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    doc.set_metadata({"title": "Integration Pipeline Test Document"})
    page = doc.new_page(width=595, height=842)
    page.insert_text(pymupdf.Point(50, 50), "1.0 Verification Section", fontsize=14)
    page.insert_text(
        pymupdf.Point(50, 100),
        "For documentation, refer to the Official Python Portal or test resource.",
        fontsize=11,
    )
    rect = pymupdf.Rect(50, 90, 200, 110)
    page.insert_link({
        "kind": pymupdf.LINK_URI,
        "from": rect,
        "uri": "https://www.python.org",
    })
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def test_full_pipeline_upload_parse_scan(client, monkeypatch):
    # Mock network validation so integration test is deterministic and fast
    async def mock_validate_url(url, normalized_url=None, use_cache=True):
        return LinkValidationResult(
            url=url,
            normalized_url=normalized_url or url,
            status="VALID",
            status_code=200,
            final_url=url,
            redirect_count=0,
            response_time_ms=120.5,
            content_type="text/html",
            error_message=None,
            validation_timestamp=pymupdf.get_text_length(""),  # dummy call
        )

    # 1. UPLOAD: POST /api/documents/upload
    pdf_bytes = create_sample_pdf_bytes()
    response = client.post(
        "/api/documents/upload",
        files={"file": ("integration_test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201
    doc_data = response.json()
    doc_id = doc_data["document_id"]
    assert doc_data["filename"] == "integration_test.pdf"
    assert doc_data["document_title"] == "Integration Pipeline Test Document"
    assert doc_data["links_count"] >= 1

    # 2. VERIFY EXTRACTION: GET /api/documents/{id}
    doc_detail_resp = client.get(f"/api/documents/{doc_id}")
    assert doc_detail_resp.status_code == 200
    doc_detail = doc_detail_resp.json()
    assert len(doc_detail["links"]) >= 1
    link_item = doc_detail["links"][0]
    link_id = link_item["link_id"]
    assert link_item["original_url"] == "https://www.python.org"

    # 3. VERIFY CONTEXT: GET /api/links/{id}
    link_detail_resp = client.get(f"/api/links/{link_id}")
    assert link_detail_resp.status_code == 200
    link_detail = link_detail_resp.json()
    assert link_detail["context"] is not None
    assert "Verification Section" in link_detail["context"]["section_heading"]
    assert link_detail["context"]["url_tokens"]["domain"] == "www.python.org"

    # 4. SCAN: POST /api/documents/{id}/scan
    scan_resp = client.post(f"/api/documents/{doc_id}/scan")
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    assert scan_data["scan_status"] == "COMPLETED"
    assert scan_data["total_links"] >= 1

    # 5. AUDIT LOGS: GET /api/audit-logs
    audit_resp = client.get(f"/api/audit-logs?document_id={doc_id}")
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    actions = [log["action_type"] for log in logs]
    assert "DOCUMENT_UPLOADED" in actions
    assert "LINK_EXTRACTED" in actions
    assert "SCAN_STARTED" in actions
    assert "SCAN_COMPLETED" in actions
