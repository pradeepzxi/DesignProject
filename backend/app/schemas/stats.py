"""Dashboard & Statistics Schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DistributionItem(BaseModel):
    name: str
    value: int
    percentage: float
    color: Optional[str] = None


class DashboardOverviewResponse(BaseModel):
    total_documents: int
    scanned_documents: int
    total_links: int
    valid_links: int
    broken_links: int
    redirected_links: int
    failed_links: int
    pending_links: int

    status_distribution: List[DistributionItem]
    failure_distribution: List[DistributionItem]
    recent_activity: List[Dict[str, Any]]
