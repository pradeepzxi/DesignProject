"""Existing Application Algorithm (Preserved Legacy Model).

Preserves the original 6-factor heuristic model from Prompt 1 / Prompt 2:
- 0.40 * semantic_similarity (via 512-dim MD5 feature hashing fallback)
- 0.20 * title_similarity (difflib SequenceMatcher ratio + token overlap)
- 0.15 * url_similarity (path token overlap + ratio)
- 0.10 * keyword_overlap (source keywords in candidate text)
- 0.10 * domain_score (netloc compatibility check)
- 0.05 * content_quality_score (text length / accessibility)

Standardized to conform to the BaseRankingAlgorithm common interface.
"""

from typing import Any, Dict, List, Optional
from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    normalize_candidate,
)
from backend.app.services.semantic_similarity_service import similarity_service
from backend.app.services.candidate_ranking_service import HybridCandidateRankingService, DEFAULT_WEIGHTS


class ExistingApplicationRanker(BaseRankingAlgorithm):
    """Preserved existing application ranking algorithm."""

    algorithm_name: str = "Existing Application Algorithm"

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self._legacy_service = HybridCandidateRankingService(weights=self.weights)

    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        custom_weights: Optional[Dict[str, float]] = None,
        disabled_features: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Execute the existing application ranking algorithm over the candidate pool."""
        if not candidates:
            return []

        normalized = [normalize_candidate(c) for c in candidates]
        broken_url = str(query_context.get("broken_url") or "")
        weights = dict(custom_weights or self.weights)
        if disabled_features:
            for feat in disabled_features:
                weights[feat] = 0.0

        evaluated = []
        for cand in normalized:
            # We call the existing similarity_service to evaluate features
            # Note: evaluate_candidate_features is an async method on similarity_service,
            # but we can call the synchronous sub-methods or calculate them synchronously:
            sem = similarity_service.calculate_title_similarity(
                anchor_text=query_context.get("anchor_text"),
                section_heading=query_context.get("section_heading"),
                candidate_title=cand.title,
            )
            # Use deterministic hash embedding for semantic similarity
            source_rep = (
                f"{query_context.get('document_title', '')} "
                f"{query_context.get('section_heading', '')} "
                f"{query_context.get('anchor_text', '')} "
                f"{query_context.get('surrounding_text', '')}"
            ).strip()
            cand_rep = f"{cand.title} {cand.content_text[:1500]}".strip()

            import re, hashlib
            import numpy as np

            # Fast deterministic sublinear hash vectorizer (exact match to legacy)
            def _get_hash_vec(txt: str) -> np.ndarray:
                tokens = re.findall(r"\b[a-zA-Z0-9]{2,}\b", txt.lower())
                char_ngrams = [txt.lower()[i:i+3] for i in range(max(0, len(txt) - 2))]
                vec = np.zeros(512, dtype=np.float32)
                for f in (tokens + char_ngrams):
                    h = int(hashlib.md5(f.encode("utf-8")).hexdigest()[:8], 16) % 512
                    vec[h] += 1.0
                vec = np.where(vec > 0, 1.0 + np.log(np.maximum(vec, 1.0)), 0.0)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec /= norm
                return vec

            if source_rep and cand_rep:
                v1 = _get_hash_vec(source_rep)
                v2 = _get_hash_vec(cand_rep)
                raw_dot = float(np.dot(v1, v2))
                calibrated_sem = float(np.clip(1.0 / (1.0 + np.exp(-12.0 * (raw_dot - 0.22))), 0.0, 1.0))
            else:
                calibrated_sem = 0.0

            title_sim = similarity_service.calculate_title_similarity(
                anchor_text=query_context.get("anchor_text"),
                section_heading=query_context.get("section_heading"),
                candidate_title=cand.title,
            )
            url_sim = similarity_service.calculate_url_similarity(broken_url, cand.candidate_url)
            kw_sc = similarity_service.calculate_keyword_overlap(
                source_keywords=query_context.get("keywords") or [],
                candidate_text=cand.content_text,
            )
            domain_sc = similarity_service.calculate_domain_score(broken_url, cand.candidate_url)
            quality_sc = similarity_service.calculate_content_quality_score(
                candidate_text=cand.content_text,
                http_status=cand.http_status,
                is_accessible=cand.is_accessible,
            )

            feats = {
                "semantic_similarity": round(calibrated_sem, 4),
                "title_similarity": round(title_sim, 4),
                "url_similarity": round(url_sim, 4),
                "keyword_overlap": round(kw_sc, 4),
                "domain_score": round(domain_sc, 4),
                "content_quality_score": round(quality_sc, 4),
            }
            if disabled_features:
                for f_name in disabled_features:
                    feats[f_name] = 0.0

            overall = self._legacy_service.calculate_overall_score(feats, custom_weights=weights)
            evaluated.append({
                "candidate": cand,
                "features": feats,
                "score": overall,
            })

        evaluated.sort(key=lambda x: x["score"], reverse=True)

        ranked_results: List[Dict[str, Any]] = []
        for idx, item in enumerate(evaluated, start=1):
            cand = item["candidate"]
            feats = item["features"]
            score = item["score"]

            explanation = self._legacy_service.generate_explanation(
                features=feats,
                rank=idx,
                context=query_context,
                candidate_title=cand.title,
            )

            ranked_results.append({
                "candidate_url": cand.candidate_url,
                "rank": idx,
                "score": score,
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
