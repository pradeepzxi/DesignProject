"""Scan Run Schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ScanRunResponse(BaseModel):
    scan_id: str
    document_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_links: int
    valid_links: int
    broken_links: int
    redirected_links: int
    failed_links: int
    scan_status: str

    model_config = ConfigDict(from_attributes=True)
