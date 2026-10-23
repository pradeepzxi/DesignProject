"""Modular Interfaces and Abstract Base Classes for Prompt 2.

This module establishes clean extension interfaces for:
- CandidateProvider: multi-source candidate discovery (sitemaps, intranet, web archive)
- SemanticSimilarityService: embedding-based text & context relevance scoring
- CandidateRankingService: multi-feature composite ranker
- ConfidenceService: decision thresholding (high confidence vs human review)
- RemediationService: autonomous document patcher / link replacement
- ReviewService: human-in-the-loop validation queue manager
- ExperimentService: benchmark suite for precision, recall, and repair accuracy
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CandidateResult:
    candidate_url: str
    source_type: str
    page_title: Optional[str] = None
    snippet: Optional[str] = None
    http_status: Optional[int] = None
    is_accessible: bool = True
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RankedCandidate:
    candidate: CandidateResult
    semantic_similarity: float
    url_similarity: float
    context_coherence: float
    composite_confidence: float
    rank: int


class CandidateProvider(ABC):
    """Abstract interface for discovering candidate replacement URLs."""

    @abstractmethod
    async def discover_candidates(
        self,
        broken_url: str,
        anchor_text: str,
        context: Dict[str, Any],
        max_candidates: int = 5,
    ) -> List[CandidateResult]:
        """Query index, search APIs, or corporate sitemaps for candidate replacements."""
        pass


class SemanticSimilarityService(ABC):
    """Abstract interface for semantic comparison between broken context and candidate pages."""

    @abstractmethod
    async def compute_similarity(
        self,
        source_context: Dict[str, Any],
        candidate_text: str,
        candidate_title: str,
    ) -> float:
        """Compute cosine similarity between context embeddings and candidate representations."""
        pass


class CandidateRankingService(ABC):
    """Abstract interface for ranking candidates using multi-factor feature fusion."""

    @abstractmethod
    async def rank_candidates(
        self,
        broken_url: str,
        context: Dict[str, Any],
        candidates: List[CandidateResult],
    ) -> List[RankedCandidate]:
        """Rank candidates using combined URL syntactic similarity and semantic embeddings."""
        pass


class ConfidenceService(ABC):
    """Abstract interface for calculating composite confidence score and determining routing."""

    @abstractmethod
    def evaluate_routing(
        self,
        top_candidate: RankedCandidate,
        high_confidence_threshold: float = 0.85,
    ) -> str:
        """Evaluate if candidate qualifies for 'AUTO_REMEDIATION' or requires 'HUMAN_REVIEW'."""
        pass


class RemediationService(ABC):
    """Abstract interface for document patchers that update hyperlinks in original files."""

    @abstractmethod
    async def apply_remediation(
        self,
        document_id: str,
        link_id: str,
        replacement_url: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Safely patch the target document without corrupting layout or metadata."""
        pass


class ReviewService(ABC):
    """Abstract interface for managing human review queue and manual approvals."""

    @abstractmethod
    async def submit_for_review(
        self,
        link_id: str,
        candidates: List[RankedCandidate],
        priority: str = "MEDIUM",
    ) -> str:
        """Enqueue link for human review."""
        pass

    @abstractmethod
    async def resolve_review(
        self,
        queue_id: str,
        approved_candidate_url: Optional[str],
        reviewer_id: str,
        decision: str,
    ) -> bool:
        """Process reviewer decision."""
        pass


class ExperimentService(ABC):
    """Abstract interface for benchmark dataset evaluation and ablation studies."""

    @abstractmethod
    async def run_experiment(
        self,
        dataset_name: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run reproducible evaluation measuring precision, recall, and repair success."""
        pass
