"""BM25 (Best Matching 25) Candidate Ranking Algorithm.

A probabilistic relevance retrieval algorithm based on the Okapi BM25 formula.
Term frequency and document length are normalized using configurable k1 and b parameters,
with standard non-negative Robertson/Lucene IDF formulation:
    IDF(q) = ln(1.0 + (N - n(q) + 0.5) / (n(q) + 0.5))
"""

import math
import re
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    extract_candidate_text,
    extract_query_text,
    normalize_candidate,
)


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric lowercased tokenization for BM25."""
    return re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())


class BM25Ranker(BaseRankingAlgorithm):
    """Clean BM25 probabilistic relevance ranking algorithm."""

    algorithm_name: str = "BM25"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 with configurable hyper-parameters.

        Args:
            k1: Term frequency saturation parameter (typically 1.2 to 2.0).
            b: Document length normalization parameter (0.0 = no normalization, 1.0 = full).
        """
        self.k1 = float(k1)
        self.b = float(b)

    def calculate_bm25_scores(
        self,
        tokenized_query: List[str],
        tokenized_corpus: List[List[str]],
        k1: float,
        b: float,
    ) -> List[float]:
        """Compute standard Okapi BM25 scores with non-negative Lucene/Robertson IDF."""
        corpus_size = len(tokenized_corpus)
        if corpus_size == 0 or not tokenized_query:
            return [0.0] * corpus_size

        doc_lengths = [len(doc) for doc in tokenized_corpus]
        avgdl = sum(doc_lengths) / max(corpus_size, 1)

        # Document frequencies for all unique tokens in corpus
        df: Dict[str, int] = {}
        for doc in tokenized_corpus:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1

        scores: List[float] = []
        for doc_tokens, doc_len in zip(tokenized_corpus, doc_lengths):
            # Term frequencies in this document
            tf: Dict[str, int] = {}
            for t in doc_tokens:
                tf[t] = tf.get(t, 0) + 1

            doc_score = 0.0
            for q_term in tokenized_query:
                n_docs = df.get(q_term, 0)
                if n_docs > 0 and q_term in tf:
                    # Non-negative Robertson/Lucene IDF formulation
                    idf = math.log(1.0 + (corpus_size - n_docs + 0.5) / (n_docs + 0.5))
                    term_freq = tf[q_term]
                    numerator = term_freq * (k1 + 1.0)
                    denominator = term_freq + k1 * (1.0 - b + b * (doc_len / max(avgdl, 1e-6)))
                    doc_score += idf * (numerator / denominator)

            scores.append(float(doc_score))

        return scores

    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        k1: Optional[float] = None,
        b: Optional[float] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Rank candidates using Okapi BM25."""
        if not candidates:
            return []

        active_k1 = float(k1) if k1 is not None else self.k1
        active_b = float(b) if b is not None else self.b

        normalized = [normalize_candidate(c) for c in candidates]
        query_text = extract_query_text(query_context)
        candidate_texts = [extract_candidate_text(c) for c in normalized]

        query_tokens = tokenize(query_text)
        tokenized_corpus = [tokenize(t) for t in candidate_texts]

        # Edge case: empty query or completely empty corpus
        if not query_tokens or not any(tokenized_corpus):
            return self._build_ranked_output(
                normalized,
                raw_scores=[0.0] * len(normalized),
                query_tokens=query_tokens,
            )

        raw_scores = self.calculate_bm25_scores(
            tokenized_query=query_tokens,
            tokenized_corpus=tokenized_corpus,
            k1=active_k1,
            b=active_b,
        )

        return self._build_ranked_output(normalized, raw_scores, query_tokens)

    def _build_ranked_output(
        self,
        candidates: List[NormalizedCandidate],
        raw_scores: List[float],
        query_tokens: List[str],
    ) -> List[Dict[str, Any]]:
        """Construct normalized scores, sort by BM25 descending, and build result records."""
        max_score = max(raw_scores) if raw_scores else 0.0

        scored_candidates = []
        for orig_idx, (cand, raw_s) in enumerate(zip(candidates, raw_scores)):
            if max_score > 0:
                # Soft saturation normalization preserving ordering: s / (s + 10.0)
                norm_score = raw_s / (raw_s + 10.0)
            else:
                norm_score = 0.0
            scored_candidates.append((orig_idx, cand, raw_s, norm_score))

        # Sort descending by raw BM25 score; tiebreak with original index
        scored_candidates.sort(key=lambda item: (item[2], -item[0]), reverse=True)

        ranked_results: List[Dict[str, Any]] = []
        for rank_idx, (orig_idx, cand, raw_s, norm_s) in enumerate(scored_candidates, start=1):
            rounded_raw = round(float(raw_s), 4)
            rounded_score = round(float(norm_s), 4)
            explanation = (
                f"Candidate ranked #{rank_idx} by Okapi BM25 "
                f"(raw score: {rounded_raw}, normalized: {rounded_score}) "
                f"based on query term matches: {', '.join(query_tokens[:5]) or 'none'}."
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
                    "bm25_raw": rounded_raw,
                    "bm25_normalized": rounded_score,
                    "k1": self.k1,
                    "b": self.b,
                },
                "explanation": explanation,
                "http_status": cand.http_status,
                "is_accessible": cand.is_accessible,
                "metadata": cand.metadata,
            })

        return ranked_results
