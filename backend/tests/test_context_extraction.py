"""Unit Tests for Linguistic and Context Extraction."""

from backend.app.services.link_context_service import LinkContextService


def test_sentence_extraction():
    paragraph = (
        "Employees can submit requests quarterly. "
        "The latest employee leave policy can be downloaded here for review. "
        "Please direct questions to human resources."
    )
    anchor = "downloaded here"
    sentence = LinkContextService.extract_sentence(paragraph, anchor)
    assert sentence == "The latest employee leave policy can be downloaded here for review."


def test_keyword_extraction():
    text = (
        "Enterprise cloud infrastructure disaster recovery, database replication, "
        "failover protocols, and cybersecurity incident response."
    )
    keywords = LinkContextService.extract_keywords(text, max_keywords=5)
    assert len(keywords) <= 5
    assert any(k in ["disaster", "recovery", "infrastructure", "replication", "cloud"] for k in keywords)


def test_build_structured_context():
    ctx = LinkContextService.build_structured_context(
        url="https://example.com/hr/leave/leave-policy-2024.pdf",
        anchor_text="Download Leave Policy",
        paragraph_text="The latest employee leave policy can be downloaded here. Review before applying.",
        section_heading="Annual Leave",
        document_title="Employee Leave Policy",
    )

    assert ctx["anchor_text"] == "Download Leave Policy"
    assert ctx["section_heading"] == "Annual Leave"
    assert ctx["document_title"] == "Employee Leave Policy"
    assert ctx["url_tokens"]["filename"] == "leave-policy-2024.pdf"
    assert len(ctx["keywords"]) > 0
