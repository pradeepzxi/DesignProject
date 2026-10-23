"""Experiment and Benchmark Schemas."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExperimentRunBase(BaseModel):
    experiment_name: str
    configuration: Dict[str, Any]
    dataset_version: str = "v1.0"
    status: str = "COMPLETED"


class ExperimentRunResponse(ExperimentRunBase):
    experiment_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ExperimentTriggerRequest(BaseModel):
    experiment_name: str
    method: str = "PROPOSED_HYBRID"  # BASELINE_URL, BASELINE_LEXICAL, SEMANTIC_ONLY, PROPOSED_HYBRID, HYBRID_REMEDIATION
    dataset_version: str = "v1.0"
    weights: Optional[Dict[str, float]] = None
    disabled_features: Optional[List[str]] = None


class MetricsSummaryResponse(BaseModel):
    total_test_cases: int
    detection_accuracy: float
    detection_precision: float
    detection_recall: float
    detection_f1: float
    top1_accuracy: float
    top3_accuracy: float
    mrr: float
    automatic_repair_precision: float
    automatic_repair_rate: float
    false_repair_rate: float
    human_review_rate: float
    avg_latency_ms: float
    by_failure_type: Dict[str, Dict[str, float]]
