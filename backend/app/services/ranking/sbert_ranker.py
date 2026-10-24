"""Sentence-BERT (SBERT) + Cosine Similarity Candidate Ranking Algorithm.

A dense semantic retrieval model using true SentenceTransformers (all-MiniLM-L6-v2).
Computes dense 384-dimensional contextual embeddings and measures semantic similarity
via cosine distance in embedding space.

Features:
- Lazy model loading on CPU
- Singleton model caching
- In-memory embedding cache for candidate texts
- Batch encoding for candidate corpora
- Clear error reporting when SBERT dependencies/models are unavailable (never silently falls back to hash vectorizer)
"""

import hashlib
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.core.logging_config import logger
from backend.app.services.ranking.base import (
    BaseRankingAlgorithm,
    NormalizedCandidate,
    extract_candidate_text,
    extract_query_text,
    normalize_candidate,
)

# Global singleton cache for the loaded transformer model
_SBERT_MODEL = None
_SBERT_LOAD_ATTEMPTED = False
_SBERT_LOAD_ERROR: Optional[str] = None


class SBERTUnavailableError(RuntimeError):
    """Raised when Sentence-BERT model cannot be loaded or executed."""
    pass


def get_sbert_model(model_name: str = "all-MiniLM-L6-v2", force_reload: bool = False):
    """Lazily load and cache the SentenceTransformer model on CPU."""
    global _SBERT_MODEL, _SBERT_LOAD_ATTEMPTED, _SBERT_LOAD_ERROR

    if force_reload:
        _SBERT_MODEL = None
        _SBERT_LOAD_ATTEMPTED = False
        _SBERT_LOAD_ERROR = None

    if _SBERT_MODEL is not None:
        return _SBERT_MODEL

    _SBERT_LOAD_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer model '{model_name}' on CPU...")
        _SBERT_MODEL = SentenceTransformer(model_name, device="cpu")
        logger.info(f"SentenceTransformer '{model_name}' loaded successfully.")
        return _SBERT_MODEL
    except Exception as exc:
        _SBERT_LOAD_ERROR = str(exc)
        logger.error(f"Failed to load SentenceTransformer: {exc}")
        raise SBERTUnavailableError(
            f"SBERT unavailable: could not load model '{model_name}'. Detail: {exc}"
        ) from exc


class SBERTRanker(BaseRankingAlgorithm):
    """Dense semantic retrieval ranker using true Sentence-BERT embeddings."""

    algorithm_name: str = "SBERT + Cosine"

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        force_unavailable: bool = False,
    ):
        """Initialize SBERT ranker with lazy loading.

        Args:
            model_name: Hugging Face model identifier (default: 'all-MiniLM-L6-v2').
            batch_size: Batch size for candidate encoding.
            force_unavailable: Test parameter to simulate missing/failed model environment.
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.force_unavailable = force_unavailable
        self._embedding_cache: Dict[str, np.ndarray] = {}

    def is_available(self) -> bool:
        """Check whether SentenceTransformer is loadable without throwing an unhandled exception."""
        if self.force_unavailable:
            return False
        try:
            get_sbert_model(self.model_name)
            return True
        except Exception:
            return False

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def encode_text(self, text: str) -> np.ndarray:
        """Encode a single text string into a normalized dense embedding."""
        if self.force_unavailable:
            raise SBERTUnavailableError("SBERT unavailable: simulated unavailable environment.")

        cache_key = self._hash_text(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        model = get_sbert_model(self.model_name)
        emb = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        self._embedding_cache[cache_key] = emb
        return emb

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Encode a batch of texts into normalized dense embeddings, utilizing cache where possible."""
        if self.force_unavailable:
            raise SBERTUnavailableError("SBERT unavailable: simulated unavailable environment.")

        model = get_sbert_model(self.model_name)
        results: List[Optional[np.ndarray]] = [None] * len(texts)
        missing_indices: List[int] = []
        missing_texts: List[str] = []

        for idx, text in enumerate(texts):
            h = self._hash_text(text)
            if h in self._embedding_cache:
                results[idx] = self._embedding_cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(text)

        if missing_texts:
            encoded_missing = model.encode(
                missing_texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            for m_idx, emb in zip(missing_indices, encoded_missing):
                results[m_idx] = emb
                self._embedding_cache[self._hash_text(texts[m_idx])] = emb

        return np.vstack(results)

    def rank_candidates(
        self,
        query_context: Dict[str, Any],
        candidates: List[Any],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Rank candidates using SBERT dense vector cosine similarity."""
        if not candidates:
            return []

        if self.force_unavailable:
            raise SBERTUnavailableError("SBERT unavailable: model cannot be executed in this mode.")

        normalized = [normalize_candidate(c) for c in candidates]
        query_text = extract_query_text(query_context)
        candidate_texts = [extract_candidate_text(c) for c in normalized]

        # Handle empty query or empty candidates
        if not query_text.strip() or not any(t.strip() for t in candidate_texts):
            return self._build_ranked_output(
                normalized,
                scores=[0.0] * len(normalized),
                query_text=query_text,
            )

        # Get query embedding
        query_emb = self.encode_text(query_text)

        # Batch encode candidates
        cand_embs = self.encode_batch(candidate_texts)

        # Cosine similarity: since embeddings are L2-normalized, dot product is cosine similarity
        raw_cosines = np.dot(cand_embs, query_emb)
        # Rescale [-1.0, 1.0] to [0.0, 1.0] for standard retrieval score representation
        scores = [float(np.clip((c + 1.0) / 2.0, 0.0, 1.0)) for c in raw_cosines]

        return self._build_ranked_output(normalized, scores, query_text)

    def _build_ranked_output(
        self,
        candidates: List[NormalizedCandidate],
        scores: List[float],
        query_text: str,
    ) -> List[Dict[str, Any]]:
        """Sort candidates by cosine similarity descending and construct standardized records."""
        paired = list(enumerate(zip(candidates, scores)))
        # Sort descending by score, tiebreak on original index
        paired.sort(key=lambda item: (item[1][1], -item[0]), reverse=True)

        ranked_results: List[Dict[str, Any]] = []
        for rank_idx, (orig_idx, (cand, score)) in enumerate(paired, start=1):
            rounded_score = round(float(score), 4)
            explanation = (
                f"Candidate ranked #{rank_idx} by Sentence-BERT (all-MiniLM-L6-v2) "
                f"with {round(rounded_score * 100, 1)}% contextual embedding similarity."
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
                    "sbert_cosine": rounded_score,
                    "model": self.model_name,
                },
                "explanation": explanation,
                "http_status": cand.http_status,
                "is_accessible": cand.is_accessible,
                "metadata": cand.metadata,
            })

        return ranked_results
