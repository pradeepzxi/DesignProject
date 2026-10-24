"""Unit tests for Candidate Ranking Algorithms.

Covers:
- TF-IDF + Cosine
- BM25
- SBERT + Cosine
- Hybrid Multi-Factor
- Existing Application Algorithm
- Factory instantiation and common schema validation
"""

import numpy as np
import pytest

from backend.app.services.ranking import (
    BaseRankingAlgorithm,
    TfidfCosineRanker,
    BM25Ranker,
    SBERTRanker,
    SBERTUnavailableError,
    HybridRanker,
    ExistingApplicationRanker,
    get_ranker,
    ALGORITHM_REGISTRY,
)


@pytest.fixture
def sample_query():
    return {
        "broken_url": "https://intranet.corp/hr/old-leave-policy-2021.html",
        "document_title": "Enterprise Employee Handbook 2024",
        "section_heading": "Statutory Annual Leave and Absence",
        "anchor_text": "Updated Absence and Sick Leave Policy",
        "surrounding_text": "Employees requesting statutory absence must refer to the Updated Absence and Sick Leave Policy on the portal.",
        "keywords": ["leave", "absence", "sick", "statutory", "portal"],
    }


@pytest.fixture
def sample_candidates():
    return [
        {
            "candidate_url": "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
            "title": "Enterprise Employee Leave and Statutory Absence Policy 2024",
            "snippet": "Updated annual leave schedule, statutory sick pay calculation, and HR portal guidelines.",
            "content_text": "Enterprise Employee Leave and Statutory Absence Policy 2024. All employees receive 25 days statutory paid leave. Sick leave and family absence must be logged via the portal.",
            "domain": "intranet.corp",
            "http_status": 200,
            "is_accessible": True,
        },
        {
            "candidate_url": "https://intranet.corp/security/vpn-access-guide.html",
            "title": "Corporate VPN Access and Multi-Factor Authentication Standard",
            "snippet": "Configuration of corporate VPN, tokens, and hardware security keys.",
            "content_text": "Corporate VPN Access and MFA Standard. Instructions for connecting securely to enterprise network.",
            "domain": "intranet.corp",
            "http_status": 200,
            "is_accessible": True,
        },
        {
            "candidate_url": "https://intranet.corp/finance/travel-reimbursement.html",
            "title": "Corporate Expense Reimbursement and Per Diem Policy",
            "snippet": "Travel expenses, vouchers, and per diem lodging limits.",
            "content_text": "Guidelines for submitting travel vouchers, per diem meal calculations, and expense audit requirements.",
            "domain": "intranet.corp",
            "http_status": 200,
            "is_accessible": True,
        },
    ]


# ==============================================================================
# 1. TF-IDF + Cosine Tests
# ==============================================================================

def test_tfidf_normal_ranking(sample_query, sample_candidates):
    ranker = TfidfCosineRanker()
    ranked = ranker.rank_candidates(sample_query, sample_candidates)

    assert len(ranked) == len(sample_candidates)
    # Check minimum required fields
    for r in ranked:
        assert "candidate_url" in r
        assert "rank" in r
        assert "score" in r
        assert "algorithm" in r
        assert r["algorithm"] == "TF-IDF + Cosine"
        assert 0.0 <= r["score"] <= 1.0

    # Ranks must be 1, 2, 3
    assert [r["rank"] for r in ranked] == [1, 2, 3]

    # Scores must be in descending order
    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)

    # Relevant HR candidate must rank first
    assert ranked[0]["candidate_url"] == "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
    assert ranked[0]["score"] > 0.3


def test_tfidf_empty_query(sample_candidates):
    ranker = TfidfCosineRanker()
    ranked = ranker.rank_candidates({}, sample_candidates)
    assert len(ranked) == len(sample_candidates)
    assert all(r["score"] == 0.0 for r in ranked)
    assert [r["rank"] for r in ranked] == [1, 2, 3]


def test_tfidf_empty_candidates(sample_query):
    ranker = TfidfCosineRanker()
    ranked = ranker.rank_candidates(sample_query, [])
    assert ranked == []


def test_tfidf_candidate_with_empty_text(sample_query):
    ranker = TfidfCosineRanker()
    candidates = [{"candidate_url": "https://empty.example.com", "title": "", "content_text": ""}]
    ranked = ranker.rank_candidates(sample_query, candidates)
    assert len(ranked) == 1
    assert ranked[0]["rank"] == 1
    assert ranked[0]["score"] == 0.0


def test_tfidf_duplicate_candidates(sample_query, sample_candidates):
    ranker = TfidfCosineRanker()
    duplicates = sample_candidates + [sample_candidates[0]]
    ranked = ranker.rank_candidates(sample_query, duplicates)
    assert len(ranked) == 4
    assert ranked[0]["score"] == ranked[1]["score"]
    assert [r["rank"] for r in ranked] == [1, 2, 3, 4]


def test_tfidf_deterministic(sample_query, sample_candidates):
    ranker = TfidfCosineRanker()
    run1 = ranker.rank_candidates(sample_query, sample_candidates)
    run2 = ranker.rank_candidates(sample_query, sample_candidates)
    assert [r["score"] for r in run1] == [r["score"] for r in run2]
    assert [r["candidate_url"] for r in run1] == [r["candidate_url"] for r in run2]


# ==============================================================================
# 2. BM25 Tests
# ==============================================================================

def test_bm25_normal_ranking(sample_query, sample_candidates):
    ranker = BM25Ranker(k1=1.5, b=0.75)
    ranked = ranker.rank_candidates(sample_query, sample_candidates)

    assert len(ranked) == len(sample_candidates)
    for r in ranked:
        assert "candidate_url" in r
        assert "rank" in r
        assert "score" in r
        assert "algorithm" in r
        assert r["algorithm"] == "BM25"
        assert 0.0 <= r["score"] <= 1.0
        assert "bm25_raw" in r["features"]

    # Scores must be sorted descending
    raw_scores = [r["features"]["bm25_raw"] for r in ranked]
    assert raw_scores == sorted(raw_scores, reverse=True)

    # Relevant HR candidate must rank first with highest score
    assert ranked[0]["candidate_url"] == "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
    assert ranked[0]["features"]["bm25_raw"] > 0.0


def test_bm25_configurable_params(sample_query, sample_candidates):
    ranker1 = BM25Ranker(k1=1.2, b=0.75)
    ranker2 = BM25Ranker(k1=2.0, b=0.3)
    res1 = ranker1.rank_candidates(sample_query, sample_candidates)
    res2 = ranker2.rank_candidates(sample_query, sample_candidates)

    assert len(res1) == 3
    assert len(res2) == 3
    assert res1[0]["features"]["k1"] == 1.2
    assert res2[0]["features"]["k1"] == 2.0


def test_bm25_empty_query(sample_candidates):
    ranker = BM25Ranker()
    ranked = ranker.rank_candidates({}, sample_candidates)
    assert len(ranked) == len(sample_candidates)
    assert all(r["features"]["bm25_raw"] == 0.0 for r in ranked)


def test_bm25_empty_candidates(sample_query):
    ranker = BM25Ranker()
    ranked = ranker.rank_candidates(sample_query, [])
    assert ranked == []


def test_bm25_duplicate_candidates(sample_query, sample_candidates):
    ranker = BM25Ranker()
    duplicates = sample_candidates + [sample_candidates[0]]
    ranked = ranker.rank_candidates(sample_query, duplicates)
    assert len(ranked) == 4
    assert ranked[0]["score"] == ranked[1]["score"]


def test_bm25_deterministic(sample_query, sample_candidates):
    ranker = BM25Ranker()
    run1 = ranker.rank_candidates(sample_query, sample_candidates)
    run2 = ranker.rank_candidates(sample_query, sample_candidates)
    assert [r["score"] for r in run1] == [r["score"] for r in run2]


# ==============================================================================
# 3. SBERT + Cosine Tests
# ==============================================================================

def test_sbert_model_loading_and_embedding():
    ranker = SBERTRanker()
    assert ranker.is_available() is True
    emb = ranker.encode_text("Enterprise HR absence guidelines")
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (384,)
    # Verify L2 normalization
    norm = np.linalg.norm(emb)
    assert pytest.approx(norm, abs=1e-3) == 1.0


def test_sbert_normal_ranking(sample_query, sample_candidates):
    ranker = SBERTRanker()
    ranked = ranker.rank_candidates(sample_query, sample_candidates)

    assert len(ranked) == len(sample_candidates)
    for r in ranked:
        assert "candidate_url" in r
        assert "rank" in r
        assert "score" in r
        assert "algorithm" in r
        assert r["algorithm"] == "SBERT + Cosine"
        assert 0.0 <= r["score"] <= 1.0
        assert "sbert_cosine" in r["features"]

    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)

    # Relevant candidate must rank first
    assert ranked[0]["candidate_url"] == "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_sbert_empty_query(sample_candidates):
    ranker = SBERTRanker()
    ranked = ranker.rank_candidates({}, sample_candidates)
    assert len(ranked) == len(sample_candidates)
    assert all(r["score"] == 0.0 for r in ranked)


def test_sbert_empty_candidates(sample_query):
    ranker = SBERTRanker()
    ranked = ranker.rank_candidates(sample_query, [])
    assert ranked == []


def test_sbert_duplicate_candidates(sample_query, sample_candidates):
    ranker = SBERTRanker()
    duplicates = sample_candidates + [sample_candidates[0]]
    ranked = ranker.rank_candidates(sample_query, duplicates)
    assert len(ranked) == 4
    assert pytest.approx(ranked[0]["score"], abs=1e-4) == ranked[1]["score"]


def test_sbert_deterministic(sample_query, sample_candidates):
    ranker = SBERTRanker()
    run1 = ranker.rank_candidates(sample_query, sample_candidates)
    run2 = ranker.rank_candidates(sample_query, sample_candidates)
    assert [r["score"] for r in run1] == [r["score"] for r in run2]


def test_sbert_unavailable_behavior(sample_query, sample_candidates):
    ranker = SBERTRanker(force_unavailable=True)
    assert ranker.is_available() is False
    with pytest.raises(SBERTUnavailableError) as exc_info:
        ranker.rank_candidates(sample_query, sample_candidates)
    assert "SBERT unavailable" in str(exc_info.value)


# ==============================================================================
# 4. Hybrid Multi-Factor Tests
# ==============================================================================

def test_hybrid_normal_ranking(sample_query, sample_candidates):
    ranker = HybridRanker()
    ranked = ranker.rank_candidates(sample_query, sample_candidates)

    assert len(ranked) == len(sample_candidates)
    for r in ranked:
        assert "candidate_url" in r
        assert "rank" in r
        assert "score" in r
        assert "algorithm" in r
        assert r["algorithm"] == "Hybrid Multi-Factor"
        assert 0.0 <= r["score"] <= 1.0
        # Check that individual orthogonal features are present
        feats = r["features"]
        for expected_f in ["bm25", "sbert", "url_similarity", "anchor_similarity", "title_similarity", "keyword_overlap", "domain_score", "content_quality"]:
            assert expected_f in feats
            assert 0.0 <= feats[expected_f] <= 1.0

    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)

    # Top candidate should be the HR absence document
    assert ranked[0]["candidate_url"] == "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
    assert ranked[0]["score"] > 0.5


def test_hybrid_feature_calculation_and_weights(sample_query, sample_candidates):
    custom_weights = {
        "bm25": 0.50,
        "sbert": 0.00,
        "url_similarity": 0.50,
        "anchor_similarity": 0.00,
        "title_similarity": 0.00,
        "keyword_overlap": 0.00,
        "domain_score": 0.00,
        "content_quality": 0.00,
    }
    ranker = HybridRanker(weights=custom_weights)
    ranked = ranker.rank_candidates(sample_query, sample_candidates)
    top = ranked[0]
    expected = 0.5 * top["features"]["bm25"] + 0.5 * top["features"]["url_similarity"]
    assert pytest.approx(top["score"], abs=1e-3) == expected


def test_hybrid_normalization():
    ranker = HybridRanker()
    # Test overall score calculation normalization
    features = {
        "bm25": 1.0,
        "sbert": 1.0,
        "url_similarity": 1.0,
        "anchor_similarity": 1.0,
        "title_similarity": 1.0,
        "keyword_overlap": 1.0,
        "domain_score": 1.0,
        "content_quality": 1.0,
    }
    score = ranker.calculate_overall_score(features)
    assert pytest.approx(score, abs=1e-4) == 1.0

    zeros = {k: 0.0 for k in features}
    assert ranker.calculate_overall_score(zeros) == 0.0


def test_hybrid_empty_query(sample_candidates):
    ranker = HybridRanker()
    ranked = ranker.rank_candidates({}, sample_candidates)
    assert len(ranked) == len(sample_candidates)
    assert [r["rank"] for r in ranked] == [1, 2, 3]


def test_hybrid_empty_candidates(sample_query):
    ranker = HybridRanker()
    ranked = ranker.rank_candidates(sample_query, [])
    assert ranked == []


def test_hybrid_duplicate_candidates(sample_query, sample_candidates):
    ranker = HybridRanker()
    duplicates = sample_candidates + [sample_candidates[0]]
    ranked = ranker.rank_candidates(sample_query, duplicates)
    assert len(ranked) == 4
    assert pytest.approx(ranked[0]["score"], abs=1e-4) == ranked[1]["score"]


def test_hybrid_deterministic(sample_query, sample_candidates):
    ranker = HybridRanker()
    run1 = ranker.rank_candidates(sample_query, sample_candidates)
    run2 = ranker.rank_candidates(sample_query, sample_candidates)
    assert [r["score"] for r in run1] == [r["score"] for r in run2]


# ==============================================================================
# 5. Existing Application Algorithm Tests
# ==============================================================================

def test_existing_ranker_normal(sample_query, sample_candidates):
    ranker = ExistingApplicationRanker()
    ranked = ranker.rank_candidates(sample_query, sample_candidates)

    assert len(ranked) == len(sample_candidates)
    for r in ranked:
        assert "candidate_url" in r
        assert "rank" in r
        assert "score" in r
        assert "algorithm" in r
        assert r["algorithm"] == "Existing Application Algorithm"
        assert 0.0 <= r["score"] <= 1.0

    scores = [r["score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0]["candidate_url"] == "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"


def test_existing_ranker_empty_candidates(sample_query):
    ranker = ExistingApplicationRanker()
    ranked = ranker.rank_candidates(sample_query, [])
    assert ranked == []


# ==============================================================================
# 6. Factory and Common Schema Verification
# ==============================================================================

def test_get_ranker_factory():
    for name in ["tfidf", "bm25", "sbert", "hybrid", "existing"]:
        ranker = get_ranker(name)
        assert isinstance(ranker, BaseRankingAlgorithm)

    with pytest.raises(ValueError):
        get_ranker("non_existent_algorithm")


def test_all_algorithms_rank_same_candidate_set(sample_query, sample_candidates):
    """Verify that every single algorithm receives the exact same candidate pool and outputs compliant records."""
    algorithms = [
        TfidfCosineRanker(),
        BM25Ranker(),
        SBERTRanker(),
        HybridRanker(),
        ExistingApplicationRanker(),
    ]

    for ranker in algorithms:
        results = ranker.rank_candidates(sample_query, sample_candidates)
        assert len(results) == len(sample_candidates)
        assert [r["rank"] for r in results] == [1, 2, 3]
        for r in results:
            assert isinstance(r["candidate_url"], str)
            assert isinstance(r["rank"], int)
            assert isinstance(r["score"], float)
            assert isinstance(r["algorithm"], str)
            assert 0.0 <= r["score"] <= 1.0
            assert "features" in r
            assert "explanation" in r
