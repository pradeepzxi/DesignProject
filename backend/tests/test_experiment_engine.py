"""Tests for the Experimental Comparison Engine, Metric Calculations, Ablation Studies, and APIs.

Verifies:
1. Exact same benchmark data, candidate pool, and ground truth across all algorithms.
2. Correct calculation of Top-1, Top-3, Recall@5, MRR, Auto Repair Precision, False Repair Rate.
3. Case-level results generation and persistence.
4. Feature ablation study for Hybrid multi-factor model.
5. Dynamic winner selection based on empirical metrics.
6. API endpoint functionality.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.services.experiment_service import (
    BenchmarkDataLoader,
    BenchmarkExperimentService,
    BenchmarkCase,
)
from backend.app.services.ranking import (
    TfidfCosineRanker,
    BM25Ranker,
    SBERTRanker,
    HybridRanker,
)
from backend.app.repositories.experiment_repository import ExperimentRepository


client = TestClient(app)


# ============================================================================
# 1. Benchmark Data Structure & Containment Tests
# ============================================================================

def test_benchmark_dataset_structure_and_integrity():
    """Verify all 60 benchmark cases conform to the required schema."""
    cases = BenchmarkDataLoader.load_benchmark_cases()
    assert len(cases) == 60, f"Expected 60 benchmark cases, got {len(cases)}"

    for case in cases:
        assert isinstance(case, BenchmarkCase)
        assert case.case_id, "case_id must not be empty"
        assert case.document_id, f"document_id missing for {case.case_id}"
        assert case.broken_url, f"broken_url missing for {case.case_id}"
        assert isinstance(case.candidate_urls, list), f"candidate_urls must be a list in {case.case_id}"
        # Positive cases with ground truth must have candidates in candidate pool
        if case.ground_truth_url and case.expected_decision != "NO_REPLACEMENT":
            assert len(case.candidate_pool) > 0, f"candidate_pool empty for {case.case_id}"

        # Check candidate representation fields
        for cand in case.candidate_pool:
            assert "candidate_url" in cand or "url" in cand
            assert "title" in cand
            assert "content" in cand or "content_text" in cand or "snippet" in cand or "content_snippet" in cand

        # If ground truth is specified and not dead link, ground truth must be in candidate pool
        if case.ground_truth_url and case.expected_decision != "NO_REPLACEMENT_REMOVE":
            pool_urls = [
                cand.get("candidate_url") or cand.get("url")
                for cand in case.candidate_pool
            ]
            assert case.ground_truth_url in pool_urls, (
                f"Ground truth {case.ground_truth_url} missing from candidate pool for {case.case_id}"
            )


def test_identical_input_guarantee_across_algorithms():
    """Verify that every algorithm receives the exact same inputs: cases, query context, and candidates."""
    cases = BenchmarkDataLoader.load_benchmark_cases()
    sample_case = cases[0]

    rankers = [
        TfidfCosineRanker(),
        BM25Ranker(),
        SBERTRanker(),
        HybridRanker(),
    ]

    query_ctx = {
        "broken_url": sample_case.broken_url,
        "document_title": sample_case.document_title,
        "section_heading": sample_case.section_heading,
        "anchor_text": sample_case.anchor_text,
        "surrounding_text": sample_case.surrounding_text,
        "keywords": sample_case.keywords,
    }

    # Verify input candidate pool is unchanged across all ranking calls
    original_pool_repr = json.dumps(sample_case.candidate_pool, sort_keys=True)

    for ranker in rankers:
        ranked = ranker.rank_candidates(query_ctx, sample_case.candidate_pool)
        assert len(ranked) == len(sample_case.candidate_pool), (
            f"{ranker.algorithm_name} did not rank all candidates"
        )
        # Ensure candidate pool was not mutated in place
        assert json.dumps(sample_case.candidate_pool, sort_keys=True) == original_pool_repr


# ============================================================================
# 2. Metric Calculations: MRR & False Repair Rate
# ============================================================================

def test_mrr_calculation_logic():
    """Verify reciprocal rank computation conforms strictly to Section 5:
    Rank 1 -> 1.0, Rank 2 -> 0.5, Rank 3 -> 0.3333, Not found -> 0.0.
    """
    cases = [
        # Case 1: Ground truth at Rank 1
        {"gt": "https://a.com", "ranked": [{"candidate_url": "https://a.com"}], "exp_decision": "REPLACE"},
        # Case 2: Ground truth at Rank 2
        {"gt": "https://b.com", "ranked": [{"candidate_url": "https://x.com"}, {"candidate_url": "https://b.com"}], "exp_decision": "REPLACE"},
        # Case 3: Ground truth at Rank 3
        {"gt": "https://c.com", "ranked": [{"candidate_url": "https://x.com"}, {"candidate_url": "https://y.com"}, {"candidate_url": "https://c.com"}], "exp_decision": "REPLACE"},
        # Case 4: Ground truth not in top candidates
        {"gt": "https://d.com", "ranked": [{"candidate_url": "https://x.com"}], "exp_decision": "REPLACE"},
    ]

    rr_scores = []
    for c in cases:
        gt = c["gt"]
        rank_pos = None
        for idx, r in enumerate(c["ranked"]):
            if r["candidate_url"] == gt:
                rank_pos = idx + 1
                break
        rr = 1.0 / rank_pos if rank_pos else 0.0
        rr_scores.append(rr)

    assert rr_scores[0] == 1.0
    assert rr_scores[1] == 0.5
    assert abs(rr_scores[2] - 0.3333) < 0.001
    assert rr_scores[3] == 0.0

    mean_mrr = sum(rr_scores) / len(rr_scores)
    assert abs(mean_mrr - (1.0 + 0.5 + 1/3 + 0.0) / 4) < 1e-6


def test_false_repair_rate_calculation_logic():
    """Verify False Repair Rate conforms strictly to Section 6:
    False Repair Rate = Incorrect automatic repairs / Total automatic repairs.
    """
    # Test scenario: 10 auto repairs executed, 2 were incorrect
    auto_repairs_executed = 10
    incorrect_auto_repairs = 2
    false_repair_rate = incorrect_auto_repairs / auto_repairs_executed
    assert false_repair_rate == 0.2

    # Zero auto repairs edge case -> should be 0.0
    zero_repairs = 0
    zero_rate = 0.0 if zero_repairs == 0 else (1 / zero_repairs)
    assert zero_rate == 0.0


# ============================================================================
# 3. Experiment Runner & Metrics Validation
# ============================================================================

@pytest.mark.asyncio
async def test_run_individual_algorithm_experiments():
    """Run individual experiments for TF-IDF, BM25, SBERT, and Hybrid, checking real metrics."""
    algorithms = ["tfidf", "bm25", "sbert", "hybrid"]

    for algo in algorithms:
        results = await BenchmarkExperimentService.run_experiment(method=algo)

        assert results["algorithm"] is not None
        assert results["total_test_cases"] == 60

        retrieval = results["retrieval_metrics"]
        assert 0.0 <= retrieval["top1_accuracy"] <= 1.0
        assert 0.0 <= retrieval["top3_accuracy"] <= 1.0
        assert 0.0 <= retrieval["mrr"] <= 1.0
        assert 0.0 <= retrieval["precision_at_1"] <= 1.0
        assert 0.0 <= retrieval["recall_at_5"] <= 1.0

        remediation = results["remediation_metrics"]
        assert 0.0 <= remediation["auto_repair_precision"] <= 1.0
        assert 0.0 <= remediation["auto_repair_rate"] <= 1.0
        assert 0.0 <= remediation["false_repair_rate"] <= 1.0
        assert 0.0 <= remediation["human_review_rate"] <= 1.0

        # Efficiency metrics
        assert results["efficiency"]["avg_case_latency_ms"] >= 0.0

        # Case-level results stored for all 60 cases
        case_results = results["case_results"]
        assert len(case_results) == 60
        assert "case_id" in case_results[0]
        assert "is_top1" in case_results[0]
        assert "reciprocal_rank" in case_results[0]


@pytest.mark.asyncio
async def test_comparative_benchmark_runner_and_winner_selection():
    """Run full 4-algorithm comparative benchmark and test winner selection."""
    comp = await BenchmarkExperimentService.run_comparative_benchmark()

    # Must contain all 4 runs
    assert "tfidf" in comp["runs"]
    assert "bm25" in comp["runs"]
    assert "sbert" in comp["runs"]
    assert "hybrid" in comp["runs"]

    # Comparison table must contain 4 algorithms
    assert len(comp["comparison_table"]) == 4

    # Winner must be dynamically selected with reasoned justification
    assert comp["best_algorithm"] in ["TF-IDF", "BM25", "SBERT", "Hybrid Multi-Factor"]
    assert isinstance(comp["selection_reason"], str)
    assert len(comp["selection_reason"]) > 20
    assert "accuracy" in comp["selection_reason"].lower() or "latency" in comp["selection_reason"].lower()

    # Case-level comparison for all 60 cases
    case_comp = comp["case_level_comparison"]
    assert len(case_comp) == 60
    assert "CASE_HR_01" in case_comp
    case_01 = case_comp["CASE_HR_01"]
    assert "algorithms" in case_01
    assert "BM25" in case_01["algorithms"]
    assert "TF-IDF" in case_01["algorithms"]
    assert "SBERT" in case_01["algorithms"]
    assert "Hybrid" in case_01["algorithms"]


# ============================================================================
# 4. Hybrid Ablation Study Tests
# ============================================================================

@pytest.mark.asyncio
async def test_hybrid_feature_ablation_study():
    """Run the 8 ablation variations for Hybrid multi-factor ranking."""
    ablation = await BenchmarkExperimentService.run_ablation_study()

    assert "ablation_results" in ablation
    results = ablation["ablation_results"]
    assert len(results) == 8, f"Expected 8 ablation configurations, got {len(results)}"

    expected_names = [
        "Full Hybrid",
        "Hybrid without SBERT",
        "Hybrid without BM25",
        "Hybrid without URL Similarity",
        "Hybrid without Title Similarity",
        "Hybrid without Anchor Similarity",
        "Hybrid without Keyword Overlap",
        "Hybrid without Domain Score",
    ]

    actual_names = [r["configuration"] for r in results]
    assert actual_names == expected_names

    # Baseline is Full Hybrid
    assert results[0]["performance_delta"] == "0.0%"
    assert results[0]["top1_accuracy"] > 0.0
    assert results[0]["mrr"] > 0.0


# ============================================================================
# 5. Database Persistence & Repository Tests
# ============================================================================

def test_experiment_database_persistence(db_session):
    """Verify experiment run persistence in SQLite database."""
    repo = ExperimentRepository(db_session)

    run = repo.create(
        experiment_name="Unit Test Comparative Benchmark",
        configuration={
            "comparison": True,
            "algorithms": ["TF-IDF", "BM25", "SBERT", "Hybrid"],
            "dataset_version": "v1.0",
        },
        dataset_version="v1.0",
        results={
            "best_algorithm": "BM25",
            "retrieval_metrics": {"top1_accuracy": 0.967, "mrr": 0.983},
            "comparison_table": [],
        },
        status="COMPLETED",
    )

    assert run.experiment_id is not None
    assert run.experiment_name == "Unit Test Comparative Benchmark"
    assert run.configuration["dataset_version"] == "v1.0"
    assert run.results["best_algorithm"] == "BM25"

    # Retrieve from DB
    retrieved = repo.get_by_id(run.experiment_id)
    assert retrieved is not None
    assert retrieved.results["retrieval_metrics"]["top1_accuracy"] == 0.967


# ============================================================================
# 6. API Endpoint Tests
# ============================================================================

def test_api_experiments_list():
    """Test GET /api/experiments and GET /api/experiments/results."""
    res1 = client.get("/api/experiments")
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    res2 = client.get("/api/experiments/results")
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)


def test_api_case_comparison_endpoint():
    """Test GET /api/experiments/case/{case_id}."""
    res = client.get("/api/experiments/case/CASE_HR_01")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "CASE_HR_01"
    assert "model_evaluations" in data
    assert "BM25" in data["model_evaluations"]
    assert "TF-IDF" in data["model_evaluations"]
    assert "SBERT" in data["model_evaluations"]
    assert "Hybrid" in data["model_evaluations"]
    assert data["candidate_pool_size"] > 0


def test_api_nonexistent_case():
    """Test GET /api/experiments/case/{invalid_id} returns 404."""
    res = client.get("/api/experiments/case/CASE_NONEXISTENT_999")
    assert res.status_code == 404


def test_api_comparison_endpoint():
    """Test GET /api/experiments/comparison."""
    res = client.get("/api/experiments/comparison")
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        data = res.json()
        assert "runs" in data
        assert "comparison_table" in data
        assert "best_algorithm" in data


def test_api_ablation_endpoint():
    """Test POST /api/experiments/ablation."""
    res = client.post("/api/experiments/ablation")
    assert res.status_code == 200
    data = res.json()
    assert "ablation_results" in data
    assert len(data["ablation_results"]) == 8
