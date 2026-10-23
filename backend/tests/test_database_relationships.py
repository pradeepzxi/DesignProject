"""Unit Tests for Database Schema, Foreign Keys, and Cascades."""

from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.scan_run import ScanRun
from backend.app.models.audit_log import AuditLog


def test_database_relationships_and_cascade(db_session):
    # 1. Create Document
    doc = Document(
        filename="Security_Policy.pdf",
        file_type="pdf",
        file_size=10240,
        processing_status="COMPLETED",
        document_title="Security Policy",
        storage_path="/tmp/fake_security.pdf",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # 2. Add Link
    link = Link(
        document_id=doc.document_id,
        original_url="https://example.com/vpn",
        normalized_url="https://example.com/vpn",
        status="VALID",
        status_code=200,
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)

    # 3. Add Context
    context = LinkContext(
        link_id=link.link_id,
        anchor_text="VPN Guide",
        section_heading="Remote Access",
        document_title="Security Policy",
        keywords=["vpn", "security", "remote"],
    )
    db_session.add(context)
    db_session.commit()

    # 4. Add ScanRun
    scan = ScanRun(
        document_id=doc.document_id,
        total_links=1,
        valid_links=1,
        scan_status="COMPLETED",
    )
    db_session.add(scan)
    db_session.commit()

    # 5. Add Audit Log
    audit = AuditLog(
        document_id=doc.document_id,
        link_id=link.link_id,
        action_type="LINK_EXTRACTED",
        status="VALID",
    )
    db_session.add(audit)
    db_session.commit()

    # Verify relationships
    assert len(doc.links) == 1
    assert link.context.anchor_text == "VPN Guide"
    assert len(doc.scan_runs) == 1
    assert len(doc.audit_logs) == 1

    # Verify Cascade Delete: Deleting document should cascade-delete link and link_context
    doc_id = doc.document_id
    link_id = link.link_id
    db_session.delete(doc)
    db_session.commit()

    assert db_session.query(Document).filter(Document.document_id == doc_id).first() is None
    assert db_session.query(Link).filter(Link.link_id == link_id).first() is None
    assert db_session.query(LinkContext).filter(LinkContext.link_id == link_id).first() is None
    # Audit log should set document_id to NULL (ON DELETE SET NULL)
    retained_audit = db_session.query(AuditLog).filter(AuditLog.audit_id == audit.audit_id).first()
    assert retained_audit is not None
    assert retained_audit.document_id is None
