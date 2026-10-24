"""Hybrid Candidate Ranking and Explainability Service.

Implements the multi-factor composite ranking formula:
overall_score =
    0.40 * semantic_similarity +
    0.20 * title_similarity +
    0.15 * url_similarity +
    0.10 * keyword_overlap +
    0.10 * domain_score +
    0.05 * content_quality_score

Generates natural-language, evidence-backed explanations for every ranked candidate.
"""

from typing import List, Dict, Any, Optional
from backend.app.services.interfaces import CandidateRankingService, CandidateResult, RankedCandidate
from backend.app.services.semantic_similarity_service import similarity_service
from backend.app.core.logging_config import logger

DEFAULT_WEIGHTS = {
    "semantic_similarity": 0.40,
    "title_similarity": 0.20,
    "url_similarity": 0.15,
    "keyword_overlap": 0.10,
    "domain_score": 0.10,
    "content_quality_score": 0.05,
}


class ActiveRemediationAlgorithmState:
    _active: str = "EXISTING_DEFAULT"
    _overridden: bool = False

    @classmethod
    def get_active(cls) -> str:
        return cls._active

    @classmethod
    def is_overridden(cls) -> bool:
        return cls._overridden

    @classmethod
    def set_active(cls, algo_name: str, enable: bool = True):
        if not enable or algo_name == "EXISTING_DEFAULT":
            cls._active = "EXISTING_DEFAULT"
            cls._overridden = False
        else:
            cls._active = algo_name
            cls._overridden = True


class HybridCandidateRankingService(CandidateRankingService):
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)

    def calculate_overall_score(
        self,
        features: Dict[str, float],
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """Calculate weighted composite score normalized to [0, 1]."""
        weights = custom_weights or self.weights
        total_weight = sum(weights.values())
        if total_weight <= 0:
            return 0.0

        weighted_sum = sum(
            features.get(key, 0.0) * weight
            for key, weight in weights.items()
        )
        normalized_score = weighted_sum / total_weight
        return round(float(normalized_score), 4)

    @staticmethod
    def generate_explanation(
        features: Dict[str, float],
        rank: int,
        context: Dict[str, Any],
        candidate_title: str,
    ) -> str:
        """Generate human-understandable explanation detailing feature contributions."""
        reasons = []

        sem = features.get("semantic_similarity", 0.0)
        title_sim = features.get("title_similarity", 0.0)
        url_sim = features.get("url_similarity", 0.0)
        domain_sc = features.get("domain_score", 0.0)
        kw_sc = features.get("keyword_overlap", 0.0)

        if sem >= 0.80:
            reasons.append(f"strong semantic alignment ({round(sem * 100)}%) with the surrounding document context")
        elif sem >= 0.50:
            reasons.append(f"moderate contextual relevance ({round(sem * 100)}%)")

        if title_sim >= 0.70:
            reasons.append(f"high title similarity to section '{context.get('section_heading', 'Header')}'")

        if domain_sc >= 0.90:
            reasons.append("identical enterprise domain authority")
        elif domain_sc >= 0.70:
            reasons.append("trusted internal organizational infrastructure")

        if url_sim >= 0.60:
            reasons.append(f"matching URL path hierarchy ({round(url_sim * 100)}% path overlap)")

        if kw_sc >= 0.60:
            reasons.append(f"significant domain terminology overlap ({round(kw_sc * 100)}%)")

        if not reasons:
            reasons.append("partial structural and keyword matches")

        explanation = f"Candidate ranked #{rank} because it exhibits {', '.join(reasons)}."
        return explanation

    async def rank_candidates(
        self,
        broken_url: str,
        context: Dict[str, Any],
        candidates: List[CandidateResult],
        custom_weights: Optional[Dict[str, float]] = None,
        disabled_features: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate features, rank candidates, and produce explainable recommendations."""
        # Check if production remediation is explicitly configured to use an alternate algorithm
        if ActiveRemediationAlgorithmState.is_overridden() and not disabled_features:
            active_algo = ActiveRemediationAlgorithmState.get_active()
            try:
                from backend.app.services.ranking import get_ranker
                ranker = get_ranker(active_algo)
                raw_cands = [
                    {
                        "candidate_url": c.candidate_url,
                        "title": c.page_title or c.metadata.get("title", ""),
                        "snippet": c.snippet or "",
                        "content_text": c.metadata.get("content_text", ""),
                        "domain": c.metadata.get("domain", ""),
                        "source": c.source,
                        "http_status": c.http_status,
                        "is_accessible": c.is_accessible,
                    }
                    for c in candidates
                ]
                ranked_raw = ranker.rank_candidates(
                    query_context={
                        "broken_url": broken_url,
                        "document_title": context.get("document_title", ""),
                        "section_heading": context.get("section_heading", ""),
                        "anchor_text": context.get("anchor_text", ""),
                        "surrounding_text": context.get("surrounding_text", ""),
                        "keywords": context.get("keywords", []),
                    },
                    candidates=raw_cands,
                )
                results = []
                for r in ranked_raw:
                    score = r["score"]
                    results.append({
                        "rank": r["rank"],
                        "candidate_url": r["candidate_url"],
                        "overall_score": score,
                        "confidence_score": score,
                        "features": r.get("features", {"score": score}),
                        "explanation": f"Ranked #{r['rank']} by {ranker.algorithm_name} with score {score:.3f}.",
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "content_text": r.get("content_text", ""),
                        "domain": r.get("domain", ""),
                        "source": r.get("source", "INTRANET"),
                        "http_status": 200,
                        "is_accessible": True,
                    })
                return results
            except Exception as e:
                logger.error(f"Failed ranking via configured active algorithm {active_algo}: {e}")

        weights = dict(custom_weights or self.weights)
        if disabled_features:
            for feat in disabled_features:
                weights[feat] = 0.0

        evaluated = []

        for cand in candidates:
            # Extract content from metadata
            cand_text = cand.metadata.get("content_text", cand.snippet or "")
            cand_title = cand.page_title or cand.metadata.get("domain", "")

            # Calculate individual feature components
            features = await similarity_service.evaluate_candidate_features(
                broken_url=broken_url,
                context=context,
                candidate_url=cand.candidate_url,
                candidate_title=cand_title,
                candidate_text=cand_text,
                http_status=cand.http_status,
                is_accessible=cand.is_accessible,
            )

            # Zero out any explicitly disabled features for ablation
            if disabled_features:
                for feat in disabled_features:
                    features[feat] = 0.0

            overall_score = self.calculate_overall_score(features, custom_weights=weights)

            evaluated.append({
                "candidate": cand,
                "features": features,
                "overall_score": overall_score,
            })

        # Sort descending by overall score
        evaluated.sort(key=lambda x: x["overall_score"], reverse=True)

        ranked_results = []
        for idx, item in enumerate(evaluated):
            rank = idx + 1
            cand = item["candidate"]
            features = item["features"]
            overall = item["overall_score"]

            explanation = self.generate_explanation(
                features=features,
                rank=rank,
                context=context,
                candidate_title=cand.page_title or "",
            )

            ranked_results.append({
                "candidate_url": cand.candidate_url,
                "title": cand.page_title,
                "snippet": cand.snippet,
                "content_text": cand.metadata.get("content_text", ""),
                "domain": cand.metadata.get("domain", ""),
                "source": cand.source_type,
                "features": features,
                "overall_score": overall,
                "score": overall,
                "rank": rank,
                "algorithm": "Existing Application Algorithm",
                "explanation": explanation,
                "http_status": cand.http_status,
                "is_accessible": cand.is_accessible,
            })

        logger.info(f"Ranked {len(ranked_results)} candidates for {broken_url} (Top score: {ranked_results[0]['overall_score'] if ranked_results else 0.0})")
        return ranked_results


ranking_service = HybridCandidateRankingService()
