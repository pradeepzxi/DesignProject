"""Unit Tests for PDF Document Parsing with PyMuPDF."""

from pathlib import Path
import pymupdf
from backend.app.services.parser_service import DocumentParserService


def test_pdf_parsing_extracts_links_and_structure(tmp_path: Path):
    pdf_path = tmp_path / "test_document.pdf"

    # Create synthetic PDF
    doc = pymupdf.open()
    doc.set_metadata({"title": "Test Information Security Policy"})
    page = doc.new_page(width=595, height=842)

    page.insert_text(pymupdf.Point(50, 50), "1.0 Access Control Protocols", fontsize=14)
    page.insert_text(
        pymupdf.Point(50, 100),
        "Employees must consult the Security Matrix for access rights.",
        fontsize=11,
    )

    link_rect = pymupdf.Rect(50, 90, 200, 110)
    page.insert_link({
        "kind": pymupdf.LINK_URI,
        "from": link_rect,
        "uri": "https://example.com/security/matrix",
    })

    # Also add a plain-text embedded URL
    page.insert_text(
        pymupdf.Point(50, 150),
        "For additional information, browse https://example.com/plain-text-link",
        fontsize=11,
    )

    doc.save(pdf_path)
    doc.close()

    # Parse with service
    result = DocumentParserService.parse_pdf(pdf_path)

    assert result["document_title"] == "Test Information Security Policy"
    assert len(result["links"]) >= 2

    annot_link = next(l for l in result["links"] if "matrix" in l["original_url"])
    assert annot_link["original_url"] == "https://example.com/security/matrix"
    assert annot_link["page_number"] == 1
    assert "Access Control" in annot_link["section_heading"]
