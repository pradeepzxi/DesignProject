"""Experiment Repository."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.app.models.prompt2_placeholders import ExperimentRun


def get_utc_now():
    return datetime.now(timezone.utc)


class ExperimentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, experiment_id: str) -> Optional[ExperimentRun]:
        return self.db.query(ExperimentRun).filter(ExperimentRun.experiment_id == experiment_id).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> List[ExperimentRun]:
        return (
            self.db.query(ExperimentRun)
            .order_by(ExperimentRun.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        experiment_name: str,
        configuration: Dict[str, Any],
        dataset_version: str = "v1.0",
        results: Optional[Dict[str, Any]] = None,
        status: str = "COMPLETED",
    ) -> ExperimentRun:
        run = ExperimentRun(
            experiment_name=experiment_name,
            configuration=configuration,
            dataset_version=dataset_version,
            results=results,
            status=status,
            completed_at=get_utc_now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
