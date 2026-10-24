"""Common Interface and Base Classes for Candidate Ranking Algorithms.

Provides a unified interface:
    rank_candidates(query_context, candidates) -> List[Dict[str, Any]]

Guarantees consistent input handling and standardized output schema across all models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


@dataclass
class NormalizedCandidate:
    """Standardized internal representation of a replacement candidate."""
    candidate_url: str
    title: str = ""
    snippet: str = ""
    content_text: str = ""
    domain: str = ""
    source_type: str = "LOCAL_INTRANET"
    http_status: Optional[int] = 200
    is_accessible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


def normalize_candidate(cand: Any) -> NormalizedCandidate:
    """Coerce various candidate input types (CandidateResult, dict, string) into NormalizedCandidate."""
    if isinstance(cand, NormalizedCandidate):
        return cand

    # Handle CandidateResult (dataclass or object with attributes)
    if hasattr(cand, "candidate_url"):
        meta = getattr(cand, "metadata", {}) or {}
        domain = meta.get("domain", "")
        if not domain and cand.candidate_url:
            domain = urlparse(cand.candidate_url).netloc
        content = meta.get("content_text", "") or getattr(cand, "snippet", "") or ""
        return NormalizedCandidate(
            candidate_url=cand.candidate_url,
            title=getattr(cand, "page_title", "") or meta.get("title", "") or "",
            snippet=getattr(cand, "snippet", "") or "",
            content_text=content,
            domain=domain,
            source_type=getattr(cand, "source_type", "LOCAL_INTRANET") or "LOCAL_INTRANET",
            http_status=getattr(cand, "http_status", 200),
            is_accessible=getattr(cand, "is_accessible", True),
            metadata=meta,
        )

    # Handle Dict input
    if isinstance(cand, dict):
        url = cand.get("candidate_url") or cand.get("url") or ""
        meta = cand.get("metadata") or {}
        domain = cand.get("domain") or meta.get("domain") or (urlparse(url).netloc if url else "")
        content = cand.get("content_text") or meta.get("content_text") or cand.get("snippet") or ""
        title = cand.get("title") or cand.get("page_title") or meta.get("title") or ""
        return NormalizedCandidate(
            candidate_url=url,
            title=title,
            snippet=cand.get("snippet") or "",
            content_text=content,
            domain=domain,
            source_type=cand.get("source") or cand.get("source_type") or "LOCAL_INTRANET",
            http_status=cand.get("http_status", 200),
            is_accessible=cand.get("is_accessible", True),
            metadata=meta or {k: v for k, v in cand.items() if k not in ("candidate_url", "title", "content_text")},
        )

    # Handle plain URL string
    if isinstance(cand, str):
        url = cand.strip()
        domain = urlparse(url).netloc if url else ""
        return NormalizedCandidate(
            candidate_url=url,
            domain=domain,
        )

    raise ValueError(f"Unsupported candidate type: {type(cand)}")


def extract_query_text(query_context: Dict[str, Any]) -> str:
    """Combine context signals (title, heading, anchor, surrounding text, URL tokens) into a text query."""
    parts: List[str] = []
    
    doc_title = (query_context.get("document_title") or "").strip()
    if doc_title:
        parts.append(doc_title)
        
    heading = (query_context.get("section_heading") or "").strip()
    if heading:
        parts.append(heading)
        
    anchor = (query_context.get("anchor_text") or "").strip()
    if anchor:
        parts.append(anchor)
        
    surrounding = (query_context.get("surrounding_text") or "").strip()
    if surrounding:
        parts.append(surrounding)
        
    # URL path tokens from broken_url
    broken_url = (query_context.get("broken_url") or "").strip()
    if broken_url:
        parsed = urlparse(broken_url)
        path_tokens = " ".join(re.findall(r"[a-zA-Z0-9]{2,}", parsed.path))
        if path_tokens:
            parts.append(path_tokens)
            
    # Explicit keywords if provided
    keywords = query_context.get("keywords") or []
    if keywords:
        parts.append(" ".join(str(k) for k in keywords))

    return " ".join(parts).strip()


def extract_candidate_text(cand: NormalizedCandidate) -> str:
    """Combine candidate title, snippet, content, and URL path tokens into a searchable representation."""
    parts: List[str] = []
    if cand.title:
        parts.append(cand.title)
    if cand.content_text:
        parts.append(cand.content_text[:2000])
    elif cand.snippet:
        parts.append(cand.snippet)

    if cand.candidate_url:
        parsed = urlparse(cand.candidate_url)
        path_tokens = " ".join(re.findall(r"[a-zA-Z0-9]{2,}", parsed.path))
        if path_tokens:
            parts.append(path_tokens)

    return " ".join(parts).strip()


class BaseRankingAlgorithm(ABC):
    """Abstract base class that all ranking algorithms must implement."""

    algorithm_name: str = "Base"

    @abstractmethod
    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Rank replacement candidates for a broken link given contextual cues.

        Args:
            query_context: Dictionary containing source document cues:
                - broken_url (str)
                - document_title (str, optional)
                - section_heading (str, optional)
                - anchor_text (str, optional)
                - surrounding_text (str, optional)
                - keywords (list of str, optional)
                - url_tokens (dict, optional)
            candidates: List of CandidateResult objects, candidate dicts, or URL strings.
            **kwargs: Algorithm-specific configuration options.

        Returns:
            List of ranked candidate dicts, sorted in descending order of score:
                - candidate_url (str)
                - rank (int, 1-indexed)
                - score (float)
                - algorithm (str)
                - title (str)
                - snippet (str)
                - content_text (str)
                - domain (str)
                - features (dict)
                - explanation (str)
                - http_status (int)
                - is_accessible (bool)
        """
        pass
