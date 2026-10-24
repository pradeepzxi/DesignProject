"""Hybrid Multi-Factor Candidate Ranking Algorithm.

Combines orthogonal retrieval signals across lexical, semantic, syntactic, and structural dimensions:
1. BM25 probabilistic term relevance (lexical)
2. SBERT dense embedding cosine similarity (deep semantic)
3. URL path and filename syntactic similarity
4. Anchor text containment and sequence matching
5. Section heading and document title similarity
6. Domain terminology keyword overlap
7. Enterprise domain authority and host proximity
8. Candidate resource accessibility and content quality

Formula:
    Hybrid Score = sum(w_i * feature_i) / sum(w_i)

All feature values are strictly normalized to [0.0, 1.0] before linear fusion.
Weights are fully configurable and documented with empirical baseline defaults.
"""

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import numpy as np

from backend.app.core.logging_config import logger
from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    extract_candidate_text,
    extract_query_text,
    normalize_candidate,
)
from backend.app.services.ranking.bm25_ranker import BM25Ranker, tokenize
from backend.app.services.ranking.sbert_ranker import SBERTRanker, SBERTUnavailableError

DEFAULT_HYBRID_WEIGHTS: Dict[str, float] = {
    "bm25": 0.20,
    "sbert": 0.30,
    "url_similarity": 0.15,
    "anchor_similarity": 0.10,
    "title_similarity": 0.10,
    "keyword_overlap": 0.05,
    "domain_score": 0.05,
    "content_quality": 0.05,
}


class HybridRanker(BaseRankingAlgorithm):
    """Multi-factor hybrid ranker combining BM25, SBERT, lexical, and structural features."""

    algorithm_name: str = "Hybrid Multi-Factor"

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
        sbert_model_name: str = "all-MiniLM-L6-v2",
    ):
        """Initialize hybrid ranker with configurable feature weights and sub-models."""
        self.weights = dict(weights or DEFAULT_HYBRID_WEIGHTS)
        self.bm25_ranker = BM25Ranker(k1=bm25_k1, b=bm25_b)
        self.sbert_ranker = SBERTRanker(model_name=sbert_model_name)

    @staticmethod
    def calculate_anchor_similarity(anchor_text: Optional[str], candidate_title: str) -> float:
        """Measure token overlap and string sequence similarity between anchor text and candidate title."""
        if not anchor_text or not candidate_title:
            return 0.0

        a_lower = anchor_text.lower().strip()
        t_lower = candidate_title.lower().strip()

        ratio = SequenceMatcher(None, a_lower, t_lower).ratio()
        a_tokens = set(re.findall(r"\b\w{3,}\b", a_lower))
        t_tokens = set(re.findall(r"\b\w{3,}\b", t_lower))

        if a_tokens and t_tokens:
            overlap = len(a_tokens & t_tokens) / min(len(a_tokens), len(t_tokens))
            ratio = max(ratio, overlap)

        return float(np.clip(ratio, 0.0, 1.0))

    @staticmethod
    def calculate_title_similarity(
        section_heading: Optional[str],
        document_title: Optional[str],
        candidate_title: str,
    ) -> float:
        """Measure similarity between document structure headings and candidate page title."""
        if not candidate_title:
            return 0.0

        t_lower = candidate_title.lower()
        headings_to_check = []
        if section_heading:
            headings_to_check.append(section_heading.lower().strip())
        if document_title:
            headings_to_check.append(document_title.lower().strip())

        if not headings_to_check:
            return 0.0

        max_score = 0.0
        for h in headings_to_check:
            ratio = SequenceMatcher(None, h, t_lower).ratio()
            h_tokens = set(re.findall(r"\b\w{3,}\b", h))
            t_tokens = set(re.findall(r"\b\w{3,}\b", t_lower))
            if h_tokens and t_tokens:
                overlap = len(h_tokens & t_tokens) / min(len(h_tokens), len(t_tokens))
                ratio = max(ratio, overlap)
            max_score = max(max_score, ratio)

        return float(np.clip(max_score, 0.0, 1.0))

    @staticmethod
    def calculate_url_similarity(broken_url: str, candidate_url: str) -> float:
        """Calculate syntactic overlap across URL path segments and filenames."""
        if not broken_url or not candidate_url:
            return 0.0

        p_broken = urlparse(broken_url)
        p_cand = urlparse(candidate_url)

        b_tokens = set(re.findall(r"[a-zA-Z0-9]{2,}", p_broken.path.lower()))
        c_tokens = set(re.findall(r"[a-zA-Z0-9]{2,}", p_cand.path.lower()))

        if not b_tokens and not c_tokens:
            return 0.7  # Both root paths

        min_len = min(len(b_tokens), len(c_tokens))
        token_overlap = len(b_tokens & c_tokens) / max(min_len, 1) if min_len > 0 else 0.0
        path_ratio = SequenceMatcher(None, p_broken.path.lower(), p_cand.path.lower()).ratio()

        score = 0.70 * token_overlap + 0.30 * path_ratio
        return float(np.clip(score, 0.0, 1.0))

    @staticmethod
    def calculate_keyword_overlap(source_keywords: List[str], candidate_text: str) -> float:
        """Fraction of salient source keywords present in candidate content."""
        if not source_keywords:
            return 0.5
        cand_lower = candidate_text.lower()
        matches = sum(1 for kw in source_keywords if str(kw).lower() in cand_lower)
        return float(np.clip(matches / len(source_keywords), 0.0, 1.0))

    @staticmethod
    def calculate_domain_score(broken_url: str, candidate_url: str) -> float:
        """Host and authority compatibility."""
        if not broken_url or not candidate_url:
            return 0.3

        d_broken = urlparse(broken_url).netloc.lower()
        d_cand = urlparse(candidate_url).netloc.lower()

        if d_broken and d_broken == d_cand:
            return 1.0

        b_parts = d_broken.split(".")
        c_parts = d_cand.split(".")
        if len(b_parts) >= 2 and len(c_parts) >= 2 and b_parts[-2:] == c_parts[-2:]:
            return 0.8

        if any(term in d_cand for term in ("corp", "internal", "intranet", "archive")):
            return 0.7

        return 0.3

    @staticmethod
    def calculate_content_quality(cand: NormalizedCandidate) -> float:
        """Resource accessibility and information density heuristic."""
        if not cand.is_accessible or (cand.http_status and cand.http_status >= 400):
            return 0.0

        length = len(cand.content_text or cand.snippet or "")
        if length > 500:
            return 1.0
        elif length > 150:
            return 0.7
        elif length > 50:
            return 0.4
        return 0.2

    def calculate_overall_score(
        self,
        features: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """Compute normalized linear fusion score in [0.0, 1.0]."""
        active_weights = weights or self.weights
        total_weight = sum(active_weights.values())
        if total_weight <= 0:
            return 0.0

        weighted_sum = sum(
            features.get(k, 0.0) * w
            for k, w in active_weights.items()
        )
        return round(float(np.clip(weighted_sum / total_weight, 0.0, 1.0)), 4)

    def generate_explanation(
        self,
        features: Dict[str, float],
        rank: int,
        query_context: Dict[str, Any],
        candidate_title: str,
    ) -> str:
        """Produce evidence-backed justification for the hybrid rank."""
        reasons = []

        bm25_s = features.get("bm25", 0.0)
        sbert_s = features.get("sbert", 0.0)
        url_s = features.get("url_similarity", 0.0)
        anchor_s = features.get("anchor_similarity", 0.0)
        domain_s = features.get("domain_score", 0.0)

        if sbert_s >= 0.75:
            reasons.append(f"high deep semantic alignment ({round(sbert_s * 100)}% SBERT)")
        elif sbert_s >= 0.50:
            reasons.append(f"moderate semantic similarity ({round(sbert_s * 100)}% SBERT)")

        if bm25_s >= 0.40:
            reasons.append(f"strong lexical keyword match (BM25: {round(bm25_s, 2)})")

        if anchor_s >= 0.70:
            reasons.append(f"direct anchor phrase match with '{query_context.get('anchor_text', 'anchor')}'")

        if domain_s >= 0.90:
            reasons.append("identical corporate domain authority")

        if url_s >= 0.60:
            reasons.append(f"matching URL path hierarchy ({round(url_s * 100)}% path overlap)")

        if not reasons:
            reasons.append("partial structural and contextual relevance matches")

        return f"Candidate ranked #{rank} via multi-factor fusion due to {', '.join(reasons)}."

    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        custom_weights: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Rank candidates using the full multi-factor hybrid model."""
        if not candidates:
            return []

        active_weights = dict(custom_weights or self.weights)
        normalized = [normalize_candidate(c) for c in candidates]
        broken_url = str(query_context.get("broken_url") or "")
        anchor_text = query_context.get("anchor_text")
        sec_heading = query_context.get("section_heading")
        doc_title = query_context.get("document_title")
        keywords = query_context.get("keywords") or []

        # 1. Compute BM25 scores
        bm25_results = self.bm25_ranker.rank_candidates(query_context, normalized)
        bm25_map = {r["candidate_url"]: r["score"] for r in bm25_results}

        # 2. Compute SBERT scores (with graceful handling if SBERT is unavailable)
        sbert_map = {}
        sbert_available = True
        try:
            sbert_results = self.sbert_ranker.rank_candidates(query_context, normalized)
            sbert_map = {r["candidate_url"]: r["score"] for r in sbert_results}
        except SBERTUnavailableError as e:
            logger.warning(f"SBERT unavailable during hybrid ranking: {e}. Reallocating weight to lexical.")
            sbert_available = False
            # Zero out SBERT weight and scale BM25
            if "sbert" in active_weights:
                sbert_w = active_weights.pop("sbert")
                active_weights["bm25"] = active_weights.get("bm25", 0.20) + sbert_w

        # 3. Compute remaining orthogonal features per candidate
        evaluated: List[Dict[str, Any]] = []
        for cand in normalized:
            url_sim = self.calculate_url_similarity(broken_url, cand.candidate_url)
            anchor_sim = self.calculate_anchor_similarity(anchor_text, cand.title)
            title_sim = self.calculate_title_similarity(sec_heading, doc_title, cand.title)
            cand_text = extract_candidate_text(cand)
            kw_overlap = self.calculate_keyword_overlap(keywords, cand_text)
            domain_sc = self.calculate_domain_score(broken_url, cand.candidate_url)
            quality_sc = self.calculate_content_quality(cand)

            features = {
                "bm25": round(bm25_map.get(cand.candidate_url, 0.0), 4),
                "url_similarity": round(url_sim, 4),
                "anchor_similarity": round(anchor_sim, 4),
                "title_similarity": round(title_sim, 4),
                "keyword_overlap": round(kw_overlap, 4),
                "domain_score": round(domain_sc, 4),
                "content_quality": round(quality_sc, 4),
            }
            if sbert_available:
                features["sbert"] = round(sbert_map.get(cand.candidate_url, 0.0), 4)

            overall_score = self.calculate_overall_score(features, active_weights)
            evaluated.append({
                "candidate": cand,
                "features": features,
                "score": overall_score,
            })

        # Sort descending by composite score; preserve original order on ties
        evaluated.sort(key=lambda item: item["score"], reverse=True)

        ranked_results: List[Dict[str, Any]] = []
        for rank_idx, item in enumerate(evaluated, start=1):
            cand = item["candidate"]
            feats = item["features"]
            sc = item["score"]

            explanation = self.generate_explanation(
                features=feats,
                rank=rank_idx,
                query_context=query_context,
                candidate_title=cand.title,
            )

            ranked_results.append({
                "candidate_url": cand.candidate_url,
                "rank": rank_idx,
                "score": sc,
                "algorithm": self.algorithm_name,
                "title": cand.title,
                "snippet": cand.snippet,
                "content_text": cand.content_text,
                "domain": cand.domain,
                "features": feats,
                "explanation": explanation,
                "http_status": cand.http_status,
                "is_accessible": cand.is_accessible,
                "metadata": cand.metadata,
            })

        return ranked_results
