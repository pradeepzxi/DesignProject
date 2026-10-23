"""Document Schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.link import LinkResponse
from backend.app.schemas.scan_run import ScanRunResponse


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    version: int = 1
    processing_status: str = "PENDING"
    document_title: Optional[str] = None


class DocumentCreate(DocumentBase):
    storage_path: str


class DocumentResponse(DocumentBase):
    document_id: str
    upload_timestamp: datetime
    storage_path: str
    links_count: Optional[int] = 0
    valid_links_count: Optional[int] = 0
    broken_links_count: Optional[int] = 0
    last_scanned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    links: List[LinkResponse] = []
    latest_scan: Optional[ScanRunResponse] = None

    model_config = ConfigDict(from_attributes=True)
