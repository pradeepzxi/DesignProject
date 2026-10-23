"""Research Experiments API Routes."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.experiment import (
    ExperimentRunResponse,
    ExperimentTriggerRequest,
)
from backend.app.repositories.experiment_repository import ExperimentRepository
from backend.app.services.experiment_service import BenchmarkExperimentService

router = APIRouter(prefix="/experiments", tags=["Research Experiments & Benchmarking"])


@router.get("", response_model=List[ExperimentRunResponse])
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List historical experiment runs and evaluations."""
    repo = ExperimentRepository(db)
    return repo.get_all(skip=skip, limit=limit)


@router.post("/run", response_model=ExperimentRunResponse)
async def run_experiment(
    req: ExperimentTriggerRequest,
    db: Session = Depends(get_db),
):
    """Run an automated experiment on the benchmark dataset and store reproducible metrics."""
    try:
        results = await BenchmarkExperimentService.run_experiment(
            method=req.method,
            custom_weights=req.weights,
            disabled_features=req.disabled_features,
            dataset_version=req.dataset_version,
        )

        repo = ExperimentRepository(db)
        run = repo.create(
            experiment_name=req.experiment_name or f"{req.method} Benchmark",
            configuration={
                "method": req.method,
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


@router.get("/compare")
async def run_comparative_benchmark(
    db: Session = Depends(get_db),
):
    """Execute complete scientific comparison across Baseline A, Baseline B, Semantic-Only, and Proposed Hybrid."""
    try:
        comparison_data = await BenchmarkExperimentService.run_comparative_benchmark()
        
        # Also persist the proposed hybrid run in DB if not already present
        repo = ExperimentRepository(db)
        repo.create(
            experiment_name="Proposed Hybrid Benchmark",
            configuration={"method": "PROPOSED_HYBRID"},
            dataset_version="v1.0",
            results=comparison_data["runs"]["proposed_hybrid"],
            status="COMPLETED",
        )
        return comparison_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparative benchmark execution failed: {str(e)}",
        )


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
    """Retrieve extracted scientific metrics (Top-1, Top-3, MRR, Repair Precision, Latency) for an experiment."""
    repo = ExperimentRepository(db)
    run = repo.get_by_id(id)
    if not run or not run.results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Metrics for experiment {id} not found")
    return run.results
