"""Document Parsing Service for PDF and DOCX files.

Extracts titles, structural headings, paragraphs, and hyperlinks with precise
positional metadata, page numbers, and linguistic context.
Uses PyMuPDF (fitz) for PDF documents and python-docx for DOCX files.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
import docx
from docx.opc.constants import RELATIONSHIP_TYPE
from backend.app.core.logging_config import logger
from backend.app.utils.url_utils import is_valid_url_syntax, normalize_url

URL_REGEX = re.compile(r"https?://[^\s<>\"'{}|\\^`\[\]]+", re.IGNORECASE)


class DocumentParserService:
    @classmethod
    def parse_document(cls, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Dispatch document parsing according to extension/type."""
        file_type = file_type.lower().strip(".")
        if file_type == "pdf":
            return cls.parse_pdf(file_path)
        elif file_type == "docx":
            return cls.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")

    @classmethod
    def parse_pdf(cls, file_path: Path) -> Dict[str, Any]:
        """Parse PDF document using PyMuPDF (fitz)."""
        extracted_links: List[Dict[str, Any]] = []
        document_title: Optional[str] = None

        doc = pymupdf.open(file_path)
        try:
            # Metadata title if available
            metadata = doc.metadata or {}
            if metadata.get("title") and metadata["title"].strip():
                document_title = metadata["title"].strip()

            current_heading = "Document Header"

            for page_index in range(len(doc)):
                page = doc[page_index]
                page_number = page_index + 1
                page_text = page.get_text("text")

                # If title was not in metadata, inspect first page top text
                if not document_title and page_index == 0:
                    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                    if lines:
                        document_title = lines[0][:150]

                # Extract structural blocks and identify heading candidates with vertical positions
                blocks = page.get_text("blocks")
                # Block format: (x0, y0, x1, y1, text, block_no, block_type)
                heading_candidates = []
                for block in blocks:
                    if block[6] != 0:  # Skip image blocks
                        continue
                    b_text = block[4].strip()
                    if not b_text:
                        continue
                    lines = [ln.strip() for ln in b_text.splitlines() if ln.strip()]
                    if (
                        lines
                        and len(lines) == 1
                        and len(lines[0]) < 80
                        and not lines[0].endswith((".", ":", ","))
                        and not lines[0].startswith(("http://", "https://", "For additional"))
                    ):
                        heading_candidates.append((block[1], lines[0]))

                def find_section_heading(y_coord: float) -> str:
                    headings_above = [h for h in heading_candidates if h[0] <= y_coord + 5]
                    if headings_above:
                        # Return the closest heading above
                        return max(headings_above, key=lambda x: x[0])[1]
                    if heading_candidates:
                        return heading_candidates[0][1]
                    return "Document Header"

                # 1. Native PDF hyperlink annotations
                pdf_links = page.get_links()
                seen_on_page = set()

                for link_annot in pdf_links:
                    uri = link_annot.get("uri")
                    if not uri or not uri.startswith(("http://", "https://")):
                        continue

                    rect = link_annot.get("from")
                    anchor_text = ""
                    y_pos = 0.0
                    if rect:
                        rect_obj = pymupdf.Rect(rect)
                        anchor_text = page.get_textbox(rect_obj).strip()
                        y_pos = rect_obj.y0

                    section_heading = find_section_heading(y_pos)

                    # Find surrounding paragraph by checking blocks containing the rect
                    surrounding_block_text = ""
                    if rect:
                        for block in blocks:
                            if block[6] == 0:
                                b_rect = pymupdf.Rect(block[:4])
                                if b_rect.intersects(pymupdf.Rect(rect)):
                                    surrounding_block_text = block[4].strip()
                                    break

                    if not anchor_text:
                        anchor_text = uri

                    if not surrounding_block_text:
                        surrounding_block_text = page_text[:300].strip()

                    location_desc = f"Page {page_number}, Section '{section_heading}'"

                    extracted_links.append({
                        "original_url": uri,
                        "anchor_text": anchor_text,
                        "paragraph_text": surrounding_block_text,
                        "section_heading": section_heading,
                        "page_number": page_number,
                        "location_description": location_desc,
                    })
                    seen_on_page.add(uri)

                # 2. Text-embedded URLs (regex) on the page that weren't interactive annotations
                for match in URL_REGEX.finditer(page_text):
                    found_url = match.group(0).rstrip(".,;)\"'>")
                    if found_url in seen_on_page or not is_valid_url_syntax(found_url):
                        continue

                    start_pos = max(0, match.start() - 100)
                    end_pos = min(len(page_text), match.end() + 100)
                    surrounding_snippet = page_text[start_pos:end_pos].strip()

                    # Find search rect for regex match to get y_pos
                    rects = page.search_for(found_url)
                    y_pos = rects[0].y0 if rects else 0.0
                    section_heading = find_section_heading(y_pos)

                    extracted_links.append({
                        "original_url": found_url,
                        "anchor_text": found_url,
                        "paragraph_text": surrounding_snippet,
                        "section_heading": section_heading,
                        "page_number": page_number,
                        "location_description": f"Page {page_number}, Section '{section_heading}' (Plain Text)",
                    })
                    seen_on_page.add(found_url)

        finally:
            doc.close()

        return {
            "document_title": document_title or file_path.stem.replace("_", " ").title(),
            "links": extracted_links,
        }

    @classmethod
    def parse_docx(cls, file_path: Path) -> Dict[str, Any]:
        """Parse Microsoft Word DOCX document using python-docx."""
        extracted_links: List[Dict[str, Any]] = []
        document_title: Optional[str] = None

        doc = docx.Document(file_path)

        # 1. Document title from core properties if set
        if doc.core_properties.title and doc.core_properties.title.strip():
            document_title = doc.core_properties.title.strip()

        # Map relationship ID to hyperlink target URLs
        rel_map: Dict[str, str] = {}
        for r_id, rel in doc.part.rels.items():
            if rel.reltype == RELATIONSHIP_TYPE.HYPERLINK:
                target_url = rel.target_ref
                if target_url.startswith(("http://", "https://")):
                    rel_map[r_id] = target_url

        current_heading = "Document Header"
        paragraph_index = 0

        for p in doc.paragraphs:
            p_text = p.text.strip()
            if not p_text:
                continue

            paragraph_index += 1

            # Detect headings
            style_name = p.style.name.lower() if p.style and p.style.name else ""
            if "heading" in style_name or "title" in style_name:
                current_heading = p_text
                if not document_title and "title" in style_name:
                    document_title = p_text
                continue

            # If document_title is still not found and this is the first non-empty paragraph
            if not document_title and paragraph_index == 1 and len(p_text) < 100:
                document_title = p_text

            seen_in_paragraph = set()

            # 1. Native XML hyperlinks in python-docx
            # Hyperlinks are stored in `w:hyperlink` children in paragraph XML element
            for child in p._element:
                if child.tag.endswith("hyperlink"):
                    r_id = child.attrib.get(
                        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                    )
                    if r_id and r_id in rel_map:
                        target_url = rel_map[r_id]
                        # Extract anchor text from inner w:t elements
                        anchor_texts = child.xpath(".//w:t")
                        anchor = "".join(node.text for node in anchor_texts if node.text).strip()
                        if not anchor:
                            anchor = target_url

                        extracted_links.append({
                            "original_url": target_url,
                            "anchor_text": anchor,
                            "paragraph_text": p_text,
                            "section_heading": current_heading,
                            "page_number": None,  # Word documents are flow-based; page numbers are not stored statically
                            "location_description": f"Section '{current_heading}', Paragraph {paragraph_index}",
                        })
                        seen_in_paragraph.add(target_url)

            # 2. Text-embedded URLs (regex) in the paragraph
            for match in URL_REGEX.finditer(p_text):
                found_url = match.group(0).rstrip(".,;)\"'>")
                if found_url in seen_in_paragraph or not is_valid_url_syntax(found_url):
                    continue

                extracted_links.append({
                    "original_url": found_url,
                    "anchor_text": found_url,
                    "paragraph_text": p_text,
                    "section_heading": current_heading,
                    "page_number": None,
                    "location_description": f"Section '{current_heading}', Paragraph {paragraph_index} (Plain Text)",
                })
                seen_in_paragraph.add(found_url)

        return {
            "document_title": document_title or file_path.stem.replace("_", " ").title(),
            "links": extracted_links,
        }
