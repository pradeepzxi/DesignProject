"""Research Experiments API Routes.

Exposes endpoints for running reproducible benchmarks, comparing ranking algorithms,
evaluating feature ablations, and inspecting case-level predictions.
"""

import io
import csv
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.experiment import (
    ExperimentRunResponse,
    ExperimentTriggerRequest,
)
from backend.app.repositories.experiment_repository import ExperimentRepository
from backend.app.services.experiment_service import (
    BenchmarkExperimentService,
    BenchmarkDataLoader,
)

router = APIRouter(prefix="/experiments", tags=["Research Experiments & Benchmarking"])


@router.get("", response_model=List[ExperimentRunResponse])
@router.get("/results", response_model=List[ExperimentRunResponse])
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List historical experiment runs and evaluations stored in database."""
    repo = ExperimentRepository(db)
    return repo.get_all(skip=skip, limit=limit)


@router.post("/run", response_model=ExperimentRunResponse)
async def run_experiment(
    req: ExperimentTriggerRequest,
    db: Session = Depends(get_db),
):
    """Run an automated experiment on the benchmark dataset using a specified algorithm."""
    try:
        results = await BenchmarkExperimentService.run_experiment(
            method=req.method,
            custom_weights=req.weights,
            disabled_features=req.disabled_features,
            dataset_version=req.dataset_version,
        )

        repo = ExperimentRepository(db)
        algo_name = results.get("algorithm", req.method)
        run = repo.create(
            experiment_name=req.experiment_name or f"{algo_name} Benchmark",
            configuration={
                "method": req.method,
                "algorithm": algo_name,
                "weights": req.weights,
                "disabled_features": req.disabled_features,
            },
            dataset_version=req.dataset_version,
            results=results,
            status="COMPLETED",
        )
        return run
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment execution failed: {str(e)}",
        )


@router.get("/comparison")
@router.get("/compare")
@router.post("/comparison")
@router.post("/compare")
async def run_comparative_benchmark(
    rerun: bool = Query(False, description="Force re-run of comparison benchmark"),
    db: Session = Depends(get_db),
):
    """Retrieve or execute complete 4-algorithm scientific comparison across TF-IDF, BM25, SBERT, and Hybrid.

    Every model evaluates the exact same 60 test cases and candidate sets.
    Dynamically determines the winner and provides evidence-backed reasoning.
    """
    repo = ExperimentRepository(db)

    # Return cached run if available and rerun not explicitly requested
    if not rerun:
        all_runs = repo.get_all(limit=20)
        for r in all_runs:
            if r.results and isinstance(r.results, dict) and "comparison_table" in r.results:
                return r.results

        comp_file = Path("data/experiments/comparison_results.json")
        if comp_file.exists():
            try:
                with open(comp_file, "r", encoding="utf-8") as f:
                    disk_data = json.load(f)
                    if "comparison_table" in disk_data:
                        return disk_data
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No benchmark results available. Run Benchmark",
        )

    try:
        comparison_data = await BenchmarkExperimentService.run_comparative_benchmark()

        # Persist comparative run in DB
        repo.create(
            experiment_name="4-Algorithm Comparative Benchmark",
            configuration={
                "comparison": True,
                "algorithms": ["TF-IDF + Cosine", "BM25", "SBERT + Cosine", "Hybrid Multi-Factor"],
                "best_algorithm": comparison_data.get("best_algorithm"),
            },
            dataset_version="v1.0",
            results=comparison_data,
            status="COMPLETED",
        )
        return comparison_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparative benchmark execution failed: {str(e)}",
        )


@router.post("/ablation")
async def run_ablation_study():
    """Execute feature ablation study measuring performance loss when removing individual hybrid features."""
    try:
        ablation_results = await BenchmarkExperimentService.run_ablation_study()
        return ablation_results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ablation study failed: {str(e)}",
        )


@router.get("/results/{algorithm}", response_model=List[ExperimentRunResponse])
def get_results_by_algorithm(
    algorithm: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Retrieve historical experiment runs for a specific algorithm."""
    repo = ExperimentRepository(db)
    all_runs = repo.get_all(limit=100)
    filtered = []
    algo_clean = algorithm.lower().replace("-", "_").replace(" ", "_")
    for r in all_runs:
        cfg = r.configuration or {}
        m = str(cfg.get("method", "")).lower()
        a = str(cfg.get("algorithm", "")).lower()
        name = str(r.experiment_name).lower()
        if algo_clean in m or algo_clean in a or algo_clean in name:
            filtered.append(r)
            if len(filtered) >= limit:
                break
    return filtered


@router.get("/case/{case_id}")
async def get_case_comparison(case_id: str):
    """Inspect model predictions and rankings for a single benchmark case across all 4 algorithms."""
    cases = BenchmarkDataLoader.load_benchmark_cases()
    matched = next((c for c in cases if c.case_id.upper() == case_id.upper()), None)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark case '{case_id}' not found. Available cases: {[c.case_id for c in cases[:5]]}...",
        )

    # Run ranking on the case across all 4 models
    from backend.app.services.ranking import (
        TfidfCosineRanker,
        BM25Ranker,
        SBERTRanker,
        HybridRanker,
    )

    models = {
        "TF-IDF": TfidfCosineRanker(),
        "BM25": BM25Ranker(),
        "SBERT": SBERTRanker(),
        "Hybrid": HybridRanker(),
    }

    query_ctx = {
        "broken_url": matched.broken_url,
        "document_title": matched.document_title,
        "section_heading": matched.section_heading,
        "anchor_text": matched.anchor_text,
        "surrounding_text": matched.surrounding_text,
        "keywords": matched.keywords,
    }

    model_evaluations: Dict[str, Any] = {}
    gt = matched.ground_truth_url

    for name, ranker in models.items():
        if matched.candidate_pool:
            ranked = ranker.rank_candidates(query_ctx, matched.candidate_pool)
        else:
            ranked = []

        top_cand = ranked[0] if ranked else None
        rank_pos = None
        if gt:
            for idx, r in enumerate(ranked):
                if r["candidate_url"].strip().lower() == gt.strip().lower():
                    rank_pos = idx + 1
                    break

        is_correct = (rank_pos == 1) if gt else (len(ranked) == 0 or (top_cand and top_cand["score"] < 0.65))

        model_evaluations[name] = {
            "algorithm": ranker.algorithm_name,
            "top_candidate": top_cand,
            "rank_of_ground_truth": rank_pos,
            "is_correct": is_correct,
            "ranked_candidates_count": len(ranked),
            "rankings": [
                {"rank": r["rank"], "url": r["candidate_url"], "score": r["score"], "title": r["title"]}
                for r in ranked
            ],
        }

    return {
        "case_id": matched.case_id,
        "broken_url": matched.broken_url,
        "document_title": matched.document_title,
        "anchor_text": matched.anchor_text,
        "surrounding_text": matched.surrounding_text,
        "ground_truth_url": matched.ground_truth_url,
        "expected_decision": matched.expected_decision,
        "candidate_pool_size": len(matched.candidate_pool),
        "model_evaluations": model_evaluations,
    }


class ActiveAlgorithmUpdateRequest(BaseModel):
    algorithm: str
    enable: bool = True


@router.get("/active-algorithm")
def get_active_remediation_algorithm(db: Session = Depends(get_db)):
    """Retrieve the algorithm currently active for production remediation."""
    from backend.app.services.candidate_ranking_service import ActiveRemediationAlgorithmState

    comp_file = Path("data/experiments/comparison_results.json")
    best_algo = None
    if comp_file.exists():
        try:
            with open(comp_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                best_algo = d.get("best_algorithm")
        except Exception:
            pass

    return {
        "active_algorithm": ActiveRemediationAlgorithmState.get_active(),
        "is_overridden": ActiveRemediationAlgorithmState.is_overridden(),
        "best_algorithm": best_algo or "BM25",
        "available_algorithms": [
            {
                "id": "EXISTING_DEFAULT",
                "name": "Production Default Heuristic (Baseline)",
                "description": "Original multi-factor candidate ranking rules used in production",
            },
            {
                "id": "BM25",
                "name": "Okapi BM25",
                "description": "Probabilistic term frequency and inverted index scoring",
            },
            {
                "id": "TF-IDF",
                "name": "TF-IDF + Cosine",
                "description": "Classic vector space term frequency-inverse document frequency",
            },
            {
                "id": "SBERT",
                "name": "Sentence-BERT + Cosine",
                "description": "Dense transformer neural semantic embeddings",
            },
            {
                "id": "HYBRID",
                "name": "Proposed Hybrid Multi-Factor",
                "description": "Composite weighted model combining lexical, semantic, URL, and anchor signals",
            },
        ],
    }


@router.post("/active-algorithm")
def set_active_remediation_algorithm(req: ActiveAlgorithmUpdateRequest):
    """Explicitly select the ranking algorithm used for autonomous remediation."""
    from backend.app.services.candidate_ranking_service import ActiveRemediationAlgorithmState

    ActiveRemediationAlgorithmState.set_active(req.algorithm.strip(), req.enable)
    return {
        "success": True,
        "active_algorithm": ActiveRemediationAlgorithmState.get_active(),
        "is_overridden": ActiveRemediationAlgorithmState.is_overridden(),
        "message": f"Remediation ranking algorithm set to '{ActiveRemediationAlgorithmState.get_active()}'",
    }


@router.get("/export")
async def export_experiment_results(
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
):
    """Export complete experimental benchmark results in CSV or JSON for scientific publication."""
    comp_file = Path("data/experiments/comparison_results.json")
    comp_data = None
    if comp_file.exists():
        try:
            with open(comp_file, "r", encoding="utf-8") as f:
                comp_data = json.load(f)
        except Exception:
            pass

    if not comp_data:
        repo = ExperimentRepository(db)
        runs = repo.get_all(limit=10)
        for r in runs:
            if r.results and "comparison_table" in r.results:
                comp_data = r.results
                break

    if not comp_data:
        comp_data = await BenchmarkExperimentService.run_comparative_benchmark()

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["case_id", "algorithm", "rank", "candidate_url", "score", "correct", "latency_ms"])

        runs = comp_data.get("runs", {})
        algo_names = {"tfidf": "TF-IDF", "bm25": "BM25", "sbert": "SBERT", "hybrid": "Hybrid"}

        for k, algo_display in algo_names.items():
            run = runs.get(k, {})
            cases = run.get("case_results", [])
            for c in cases:
                c_id = c.get("case_id", "")
                lat = c.get("latency_ms", 0.0)
                gt = c.get("ground_truth")
                cands = c.get("top_candidates", [])
                if not cands:
                    pred_url = c.get("predicted_url", "")
                    correct = "true" if c.get("is_top1") else "false"
                    writer.writerow([c_id, algo_display, 1, pred_url, c.get("confidence", 0.0), correct, lat])
                else:
                    for r_idx, cand in enumerate(cands):
                        c_url = cand.get("url", "")
                        score = cand.get("score", 0.0)
                        rank_num = cand.get("rank", r_idx + 1)
                        is_corr = "true" if (gt and c_url.strip().lower() == gt.strip().lower()) else "false"
                        writer.writerow([c_id, algo_display, rank_num, c_url, score, is_corr, lat])

        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="algorithm_benchmark_results.csv"'},
        )
    else:
        runs = comp_data.get("runs", {})
        metrics = {}
        for k in ["tfidf", "bm25", "sbert", "hybrid"]:
            if k in runs:
                metrics[runs[k].get("algorithm", k)] = runs[k].get("retrieval_metrics", {})

        json_export = {
            "experiment": "Intelligent Link Remediation - 4-Algorithm Comparative Benchmark",
            "dataset": {
                "name": "Enterprise Document Link Integrity Benchmark",
                "version": "v1.0",
                "total_cases": 60,
                "document_types": ["PDF", "DOCX", "Intranet"],
            },
            "algorithms": [r["algorithm"] for r in comp_data.get("comparison_table", [])],
            "metrics": metrics,
            "case_results": comp_data.get("case_level_comparison", {}),
            "parameters": {
                "TF-IDF": {"analyzer": "word", "ngram_range": [1, 2], "metric": "cosine"},
                "BM25": {"k1": 1.5, "b": 0.75, "idf": "robertson_positive"},
                "SBERT": {"model": "all-MiniLM-L6-v2", "device": "cpu", "similarity": "cosine"},
                "Hybrid": {
                    "bm25_weight": 0.35,
                    "sbert_weight": 0.30,
                    "title_weight": 0.15,
                    "url_weight": 0.10,
                    "anchor_weight": 0.05,
                    "domain_weight": 0.05,
                },
            },
            "timestamp": comp_data.get("timestamp"),
            "winner": {
                "best_algorithm": comp_data.get("best_algorithm"),
                "reason": comp_data.get("selection_reason"),
            },
        }
        return json_export


@router.get("/{id}", response_model=ExperimentRunResponse)
def get_experiment_by_id(id: str, db: Session = Depends(get_db)):
    """Retrieve full details of an experiment run."""
    repo = ExperimentRepository(db)
    run = repo.get_by_id(id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment {id} not found")
    return run


@router.get("/{id}/metrics")
def get_experiment_metrics(id: str, db: Session = Depends(get_db)):
    """Retrieve extracted scientific metrics for an experiment."""
    repo = ExperimentRepository(db)
    run = repo.get_by_id(id)
    if not run or not run.results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metrics for experiment {id} not found")
    return run.results
