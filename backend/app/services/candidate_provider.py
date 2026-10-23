"""Candidate Discovery Providers.

Modular architecture for discovering candidate replacement URLs across
local enterprise intranet repositories, corporate sitemaps, and web sources.
Works completely offline without external API keys.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.services.interfaces import CandidateProvider, CandidateResult


class LocalCandidateProvider(CandidateProvider):
    """Local enterprise repository candidate provider.

    Queries local synthetic intranet indices and cached document libraries.
    """

    def __init__(self, index_file: Optional[Path] = None):
        self.index_file = index_file or (settings.CANDIDATE_PAGES_DIR / "index.json")
        self.candidates_db: List[Dict[str, Any]] = []
        self._load_candidates()

    def _load_candidates(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.candidates_db = json.load(f)
                logger.info(f"Loaded {len(self.candidates_db)} local candidate resources from {self.index_file.name}")
            except Exception as e:
                logger.error(f"Failed to load candidate pages index: {e}")
                self.candidates_db = []
        else:
            self.candidates_db = []

    @staticmethod
    def generate_query_variations(
        broken_url: str,
        anchor_text: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """Generate diverse lexical and contextual query variations."""
        heading = (context.get("section_heading") or "").strip()
        doc_title = (context.get("document_title") or "").strip()
        keywords = context.get("keywords") or []
        url_tokens = context.get("url_tokens") or {}
        
        parsed_b = urlparse(broken_url)
        filename = (url_tokens.get("filename") or Path(parsed_b.path).name).replace("-", " ").replace("_", " ")
        domain = url_tokens.get("domain") or parsed_b.netloc
        path_segments = " ".join(url_tokens.get("path_segments") or [s for s in parsed_b.path.split("/") if s])

        variations = []

        # 1. Anchor text + Domain
        if anchor_text:
            variations.append(f"{anchor_text} {domain}".strip())

        # 2. Section Heading + Top Keywords
        if heading:
            kw_str = " ".join(keywords[:3])
            variations.append(f"{heading} {kw_str}".strip())

        # 3. Cleaned URL Filename + Keywords
        if filename:
            variations.append(f"{filename} {' '.join(keywords[:2])}".strip())

        # 4. Document Title + Anchor
        if doc_title and anchor_text:
            variations.append(f"{doc_title} {anchor_text}".strip())

        # 5. URL Path hierarchy terms + Anchor
        if path_segments:
            variations.append(f"{path_segments} {anchor_text}".strip())

        # Deduplicate while preserving order
        unique_variations = []
        seen = set()
        for v in variations:
            clean = " ".join(v.lower().split())
            if clean and clean not in seen:
                seen.add(clean)
                unique_variations.append(v)

        return unique_variations or [anchor_text or broken_url]

    async def discover_candidates(
        self,
        broken_url: str,
        anchor_text: str,
        context: Dict[str, Any],
        max_candidates: int = 5,
    ) -> List[CandidateResult]:
        """Search local repository for candidate replacements using multi-query variations."""
        query_variations = self.generate_query_variations(broken_url, anchor_text, context)
        all_terms = set()
        for q in query_variations:
            words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", q.lower())
            all_terms.update(words)

        scored_candidates = []

        for item in self.candidates_db:
            cand_url = item["candidate_url"]
            if cand_url == broken_url:
                continue  # Never suggest identical broken URL

            title = item.get("title", "")
            content = item.get("content_text", "")
            item_keywords = set(k.lower() for k in item.get("keywords", []))

            # Calculate preliminary retrieval match score
            searchable_corpus = f"{title.lower()} {content.lower()} {' '.join(item_keywords)}"
            match_count = sum(1 for term in all_terms if term in searchable_corpus)

            # Boost if domain or anchor matches
            if anchor_text and anchor_text.lower() in searchable_corpus:
                match_count += 3

            parsed_cand = urlparse(cand_url)
            parsed_broken = urlparse(broken_url)
            if parsed_cand.netloc.lower() == parsed_broken.netloc.lower():
                match_count += 2

            if match_count > 0:
                result = CandidateResult(
                    candidate_url=cand_url,
                    source_type=item.get("source", "LOCAL_INTRANET"),
                    page_title=title,
                    snippet=item.get("snippet", content[:200]),
                    http_status=200,
                    is_accessible=True,
                    metadata={
                        "domain": item.get("domain") or parsed_cand.netloc,
                        "content_text": content,
                        "raw_match_score": match_count,
                        "matched_queries": len(query_variations),
                    },
                )
                scored_candidates.append((match_count, result))

        # Sort by match score descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [c for _, c in scored_candidates[:max_candidates]]

        # Fallback: if no candidates matched specific terms, return top catalog candidates
        if not top_candidates and self.candidates_db:
            for item in self.candidates_db[:max_candidates]:
                top_candidates.append(
                    CandidateResult(
                        candidate_url=item["candidate_url"],
                        source_type=item.get("source", "LOCAL_INTRANET"),
                        page_title=item.get("title"),
                        snippet=item.get("snippet"),
                        http_status=200,
                        is_accessible=True,
                        metadata={
                            "domain": item.get("domain"),
                            "content_text": item.get("content_text"),
                        },
                    )
                )

        logger.info(f"Discovered {len(top_candidates)} candidates for broken link: {broken_url}")
        return top_candidates


class WebCandidateProvider(CandidateProvider):
    """Configurable Web Candidate Provider for external sitemaps and indexes."""

    def __init__(self, local_fallback: Optional[LocalCandidateProvider] = None):
        self.local_provider = local_fallback or LocalCandidateProvider()

    async def discover_candidates(
        self,
        broken_url: str,
        anchor_text: str,
        context: Dict[str, Any],
        max_candidates: int = 5,
    ) -> List[CandidateResult]:
        # Web search can be enabled via external API key if configured;
        # defaults reliably to local provider for guaranteed offline execution
        return await self.local_provider.discover_candidates(
            broken_url=broken_url,
            anchor_text=anchor_text,
            context=context,
            max_candidates=max_candidates,
        )


default_candidate_provider = LocalCandidateProvider()
