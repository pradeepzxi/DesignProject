"""Semantic Similarity and Feature Extraction Service.

Computes:
1. semantic_similarity: Cosine similarity between context embeddings and candidate representations
   using SentenceTransformers (with fast, deterministic SVD/TF-IDF fallback).
2. title_similarity: Linguistic and token similarity between anchor/heading and candidate title.
3. url_similarity: Syntactic overlap across URL path segments and filenames.
4. keyword_overlap: Jaccard overlap of salient domain terminology.
5. domain_score: Host matching and enterprise network proximity.
6. content_quality_score: Content length, status, and information density.

All feature calculations are strictly bounded to [0.0, 1.0] and cached for efficiency.
"""

import hashlib
import os
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.core.logging_config import logger
from backend.app.services.interfaces import SemanticSimilarityService

# Try loading SentenceTransformers if installed
SENTENCE_TRANSFORMERS_AVAILABLE = False
_st_model = None

try:
    from sentence_transformers import SentenceTransformer
    # Only load lightweight model if environment permits
    if os.environ.get("USE_TRANSFORMERS", "").lower() in ("true", "1"):
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    logger.debug(f"SentenceTransformer not loaded (using fast vectorizer): {e}")


class HybridSemanticSimilarityService(SemanticSimilarityService):
    def __init__(self):
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=5000,
            sublinear_tf=True,
        )
        self.is_vectorizer_fitted = False

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def get_embedding(self, text: str) -> np.ndarray:
        """Compute and cache dense or sparse embedding for text."""
        cache_key = self._hash_text(text)
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        if SENTENCE_TRANSFORMERS_AVAILABLE and _st_model is not None:
            try:
                emb = _st_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
                self.embedding_cache[cache_key] = emb
                return emb
            except Exception as e:
                logger.warning(f"Transformer encode failed: {e}")

        # Deterministic sublinear word + character n-gram hashing vectorizer (normalized)
        tokens = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
        char_ngrams = [text.lower()[i:i+3] for i in range(max(0, len(text) - 2))]
        all_features = tokens + char_ngrams
        vec = np.zeros(512, dtype=np.float32)
        for f in all_features:
            h = int(hashlib.md5(f.encode("utf-8")).hexdigest()[:8], 16) % 512
            vec[h] += 1.0
        # Sublinear term frequency scaling: 1 + log(tf) (safe against 0)
        vec = np.where(vec > 0, 1.0 + np.log(np.maximum(vec, 1.0)), 0.0)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm

        self.embedding_cache[cache_key] = vec
        return vec

    async def compute_similarity(
        self,
        source_context: Dict[str, Any],
        candidate_text: str,
        candidate_title: str,
    ) -> float:
        """Compute cosine similarity between broken context and candidate content."""
        source_rep = (
            f"{source_context.get('document_title', '')} "
            f"{source_context.get('section_heading', '')} "
            f"{source_context.get('anchor_text', '')} "
            f"{source_context.get('surrounding_text', '')}"
        ).strip()

        candidate_rep = f"{candidate_title} {candidate_text[:1500]}".strip()

        if not source_rep or not candidate_rep:
            return 0.0

        emb1 = await self.get_embedding(source_rep)
        emb2 = await self.get_embedding(candidate_rep)

        raw_sim = float(np.dot(emb1, emb2))
        # Information Retrieval Sigmoid projection for query-to-document calibration
        calibrated_sim = 1.0 / (1.0 + np.exp(-12.0 * (raw_sim - 0.22)))
        return float(np.clip(calibrated_sim, 0.0, 1.0))

    @staticmethod
    def calculate_title_similarity(
        anchor_text: Optional[str],
        section_heading: Optional[str],
        candidate_title: Optional[str],
    ) -> float:
        """Calculate token and sequence similarity between source headings and candidate title."""
        if not candidate_title:
            return 0.0

        title_lower = candidate_title.lower()
        candidates_to_check = []
        if anchor_text:
            candidates_to_check.append(anchor_text.lower())
        if section_heading:
            candidates_to_check.append(section_heading.lower())

        if not candidates_to_check:
            return 0.0

        max_ratio = 0.0
        for src in candidates_to_check:
            ratio = SequenceMatcher(None, src, title_lower).ratio()
            src_tokens = set(re.findall(r"\b\w{3,}\b", src))
            title_tokens = set(re.findall(r"\b\w{3,}\b", title_lower))
            if src_tokens and title_tokens:
                # Overlap coefficient: measures containment of short anchor in longer title
                overlap = len(src_tokens & title_tokens) / min(len(src_tokens), len(title_tokens))
                ratio = max(ratio, overlap)
            max_ratio = max(max_ratio, ratio)

        return float(np.clip(max_ratio, 0.0, 1.0))

    @staticmethod
    def calculate_url_similarity(broken_url: str, candidate_url: str) -> float:
        """Calculate syntactic overlap across URL path segments, tokens, and filenames."""
        p_broken = urlparse(broken_url)
        p_cand = urlparse(candidate_url)

        # Path tokens (split on /, -, _, .)
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
    def calculate_keyword_overlap(
        source_keywords: List[str],
        candidate_text: str,
    ) -> float:
        """Fraction of salient source keywords present in candidate content."""
        if not source_keywords:
            return 0.5
        cand_lower = candidate_text.lower()
        matches = sum(1 for kw in source_keywords if kw.lower() in cand_lower)
        return float(np.clip(matches / len(source_keywords), 0.0, 1.0))

    @staticmethod
    def calculate_domain_score(broken_url: str, candidate_url: str) -> float:
        """Check domain compatibility."""
        d_broken = urlparse(broken_url).netloc.lower()
        d_cand = urlparse(candidate_url).netloc.lower()

        if d_broken == d_cand:
            return 1.0

        # Subdomain match
        b_parts = d_broken.split(".")
        c_parts = d_cand.split(".")
        if len(b_parts) >= 2 and len(c_parts) >= 2 and b_parts[-2:] == c_parts[-2:]:
            return 0.8

        # Enterprise intranet / authority domain
        if "corp" in d_cand or "internal" in d_cand or "intranet" in d_cand:
            return 0.7

        return 0.3

    @staticmethod
    def calculate_content_quality_score(
        candidate_text: str,
        http_status: Optional[int] = 200,
        is_accessible: bool = True,
    ) -> float:
        """Evaluate quality and accessibility of candidate resource."""
        if not is_accessible or (http_status and http_status >= 400):
            return 0.0

        length = len(candidate_text or "")
        if length > 500:
            return 1.0
        elif length > 150:
            return 0.7
        elif length > 50:
            return 0.4
        return 0.2

    async def evaluate_candidate_features(
        self,
        broken_url: str,
        context: Dict[str, Any],
        candidate_url: str,
        candidate_title: str,
        candidate_text: str,
        http_status: Optional[int] = 200,
        is_accessible: bool = True,
    ) -> Dict[str, float]:
        """Compute all six distinct feature values for a candidate."""
        semantic_sim = await self.compute_similarity(context, candidate_text, candidate_title)
        title_sim = self.calculate_title_similarity(
            anchor_text=context.get("anchor_text"),
            section_heading=context.get("section_heading"),
            candidate_title=candidate_title,
        )
        url_sim = self.calculate_url_similarity(broken_url, candidate_url)
        keyword_overlap = self.calculate_keyword_overlap(
            source_keywords=context.get("keywords") or [],
            candidate_text=candidate_text,
        )
        domain_sc = self.calculate_domain_score(broken_url, candidate_url)
        quality_sc = self.calculate_content_quality_score(
            candidate_text=candidate_text,
            http_status=http_status,
            is_accessible=is_accessible,
        )

        return {
            "semantic_similarity": round(semantic_sim, 4),
            "title_similarity": round(title_sim, 4),
            "url_similarity": round(url_sim, 4),
            "keyword_overlap": round(keyword_overlap, 4),
            "domain_score": round(domain_sc, 4),
            "content_quality_score": round(quality_sc, 4),
        }


similarity_service = HybridSemanticSimilarityService()
