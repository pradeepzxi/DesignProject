"""Candidate Ranking Algorithms Package.

Exports clean, modular implementations conforming to BaseRankingAlgorithm:
1. TF-IDF + Cosine Similarity (TfidfCosineRanker)
2. Okapi BM25 (BM25Ranker)
3. Sentence-BERT + Cosine Similarity (SBERTRanker)
4. Hybrid Multi-Factor Ranking (HybridRanker)
5. Existing Application Algorithm (ExistingApplicationRanker)
"""

from typing import Dict, Any, Type
from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    normalize_candidate,
    extract_query_text,
    extract_candidate_text,
)
from backend.app.services.ranking.tfidf_ranker import TfidfCosineRanker
from backend.app.services.ranking.bm25_ranker import BM25Ranker
from backend.app.services.ranking.sbert_ranker import SBERTRanker, SBERTUnavailableError
from backend.app.services.ranking.hybrid_ranker import HybridRanker, DEFAULT_HYBRID_WEIGHTS
from backend.app.services.ranking.existing_ranker import ExistingApplicationRanker

ALGORITHM_REGISTRY: Dict[str, Type[BaseRankingAlgorithm]] = {
    "tfidf": TfidfCosineRanker,
    "tfidf_cosine": TfidfCosineRanker,
    "bm25": BM25Ranker,
    "sbert": SBERTRanker,
    "sbert_cosine": SBERTRanker,
    "hybrid": HybridRanker,
    "hybrid_multifactor": HybridRanker,
    "existing": ExistingApplicationRanker,
    "legacy": ExistingApplicationRanker,
}


def get_ranker(algorithm_name: str, **kwargs: Any) -> BaseRankingAlgorithm:
    """Factory to retrieve a configured ranker instance by name."""
    clean_name = algorithm_name.strip().lower().replace("-", "_").replace(" ", "_").replace("+", "")
    # Remove any duplicate underscores
    while "__" in clean_name:
        clean_name = clean_name.replace("__", "_")
    clean_name = clean_name.strip("_")

    # Match aliases
    if clean_name in ALGORITHM_REGISTRY:
        return ALGORITHM_REGISTRY[clean_name](**kwargs)

    if "tfidf" in clean_name:
        return TfidfCosineRanker(**kwargs)
    elif "bm25" in clean_name:
        return BM25Ranker(**kwargs)
    elif "sbert" in clean_name:
        return SBERTRanker(**kwargs)
    elif "hybrid" in clean_name:
        return HybridRanker(**kwargs)
    elif "existing" in clean_name or "legacy" in clean_name:
        return ExistingApplicationRanker(**kwargs)

    raise ValueError(
        f"Unknown ranking algorithm '{algorithm_name}'. "
        f"Available algorithms: {list(ALGORITHM_REGISTRY.keys())}"
    )


__all__ = [
    "BaseRankingAlgorithm",
    "NormalizedCandidate",
    "normalize_candidate",
    "extract_query_text",
    "extract_candidate_text",
    "TfidfCosineRanker",
    "BM25Ranker",
    "SBERTRanker",
    "SBERTUnavailableError",
    "HybridRanker",
    "DEFAULT_HYBRID_WEIGHTS",
    "ExistingApplicationRanker",
    "get_ranker",
    "ALGORITHM_REGISTRY",
]
