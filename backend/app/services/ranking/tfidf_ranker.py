"""TF-IDF + Cosine Similarity Candidate Ranking Algorithm.

A pure information-retrieval lexical baseline that computes Term Frequency-Inverse
Document Frequency representations for query and candidates, then ranks by
cosine similarity in the vector space.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    extract_candidate_text,
    extract_query_text,
    normalize_candidate,
)


class TfidfCosineRanker(BaseRankingAlgorithm):
    """Clean TF-IDF + Cosine Similarity baseline ranker."""

    algorithm_name: str = "TF-IDF + Cosine"

    def __init__(
        self,
        ngram_range: tuple = (1, 2),
        sublinear_tf: bool = True,
        max_features: Optional[int] = 10000,
    ):
        self.ngram_range = ngram_range
        self.sublinear_tf = sublinear_tf
        self.max_features = max_features

    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Rank candidates using TF-IDF vectorization and cosine similarity."""
        if not candidates:
            return []

        normalized = [normalize_candidate(c) for c in candidates]
        query_text = extract_query_text(query_context)
        candidate_texts = [extract_candidate_text(c) for c in normalized]

        # Edge case: empty query or all empty candidate texts
        if not query_text.strip() or not any(t.strip() for t in candidate_texts):
            return self._build_ranked_output(
                normalized,
                scores=[0.0] * len(normalized),
                query_text=query_text,
            )

        # Build corpus: query at index 0, followed by candidate texts
        corpus = [query_text] + candidate_texts

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=self.ngram_range,
                stop_words="english",
                sublinear_tf=self.sublinear_tf,
                max_features=self.max_features,
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)

            # Query vector is row 0; candidates are rows 1 to N
            query_vec = tfidf_matrix[0:1]
            cand_vecs = tfidf_matrix[1:]

            # Cosine similarity between query and candidates
            cos_sims = cosine_similarity(query_vec, cand_vecs)[0]
            scores = [float(np.clip(s, 0.0, 1.0)) for s in cos_sims]
        except Exception:
            # Fallback if vocabulary is empty after stopword removal
            scores = [0.0] * len(normalized)

        return self._build_ranked_output(normalized, scores, query_text)

    def _build_ranked_output(
        self,
        candidates: List[NormalizedCandidate],
        scores: List[float],
        query_text: str,
    ) -> List[Dict[str, Any]]:
        """Sort candidates by score descending and construct standardized result records."""
        paired = list(enumerate(zip(candidates, scores)))
        # Sort by score descending; preserve original index order for ties
        paired.sort(key=lambda item: (item[1][1], -item[0]), reverse=True)

        ranked_results: List[Dict[str, Any]] = []
        for rank_idx, (orig_idx, (cand, score)) in enumerate(paired, start=1):
            rounded_score = round(float(score), 4)
            explanation = (
                f"Candidate ranked #{rank_idx} by TF-IDF cosine similarity "
                f"({round(rounded_score * 100, 1)}% vector alignment with context tokens)."
            )
            ranked_results.append({
                "candidate_url": cand.candidate_url,
                "rank": rank_idx,
                "score": rounded_score,
                "algorithm": self.algorithm_name,
                "title": cand.title,
                "snippet": cand.snippet,
                "content_text": cand.content_text,
                "domain": cand.domain,
                "features": {
                    "tfidf_cosine": rounded_score,
                },
                "explanation": explanation,
                "http_status": cand.http_status,
                "is_accessible": cand.is_accessible,
                "metadata": cand.metadata,
            })

        return ranked_results
