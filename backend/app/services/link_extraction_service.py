"""Link Extraction Service.

Coordinates document parsing, syntax validation, canonical URL normalization,
and contextual feature generation for enterprise document repositories.
"""

from typing import List, Dict, Any, Tuple
from pathlib import Path
from backend.app.services.parser_service import DocumentParserService
from backend.app.services.link_context_service import LinkContextService
from backend.app.utils.url_utils import normalize_url, is_valid_url_syntax
from backend.app.core.logging_config import logger


class LinkExtractionService:
    @classmethod
    def extract_links_from_file(
        cls, file_path: Path, file_type: str
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extract links and their rich contexts from a PDF or DOCX file.

        Returns:
            (document_title, valid_links_data, malformed_links_data)
        """
        parsed_doc = DocumentParserService.parse_document(file_path, file_type)
        document_title = parsed_doc.get("document_title", file_path.stem)
        raw_links = parsed_doc.get("links", [])

        valid_links_data = []
        malformed_links_data = []

        for item in raw_links:
            raw_url = item["original_url"]

            if not is_valid_url_syntax(raw_url):
                logger.warning(f"Malformed URL rejected: {raw_url}")
                malformed_links_data.append(item)
                continue

            try:
                norm_url = normalize_url(raw_url)
            except Exception as e:
                logger.warning(f"URL normalization failed for {raw_url}: {e}")
                malformed_links_data.append(item)
                continue

            # Build enriched research context
            context_data = LinkContextService.build_structured_context(
                url=norm_url,
                anchor_text=item.get("anchor_text"),
                paragraph_text=item.get("paragraph_text"),
                section_heading=item.get("section_heading"),
                document_title=document_title,
            )

            valid_links_data.append({
                "original_url": raw_url,
                "normalized_url": norm_url,
                "anchor_text": item.get("anchor_text"),
                "page_number": item.get("page_number"),
                "location_description": item.get("location_description"),
                "context": context_data,
            })

        logger.info(
            f"Extracted {len(valid_links_data)} valid links and {len(malformed_links_data)} "
            f"malformed links from {file_path.name}"
        )
        return document_title, valid_links_data, malformed_links_data
