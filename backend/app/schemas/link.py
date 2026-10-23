"""Link Schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.link_context import LinkContextResponse


class LinkBase(BaseModel):
    original_url: str
    normalized_url: str
    status: str = "PENDING"
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    response_time_ms: Optional[float] = None
    content_type: Optional[str] = None
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    page_number: Optional[int] = None
    location_description: Optional[str] = None


class LinkResponse(LinkBase):
    link_id: str
    document_id: str
    document_title: Optional[str] = None
    document_filename: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LinkDetailResponse(LinkResponse):
    context: Optional[LinkContextResponse] = None

    model_config = ConfigDict(from_attributes=True)


class LinkValidationResult(BaseModel):
    url: str
    normalized_url: str
    status: str  # VALID, BROKEN_404, BROKEN_4XX, SERVER_ERROR_5XX, TIMEOUT, DNS_ERROR, CONNECTION_ERROR, REDIRECT, FORBIDDEN, UNAUTHORIZED, INVALID_URL, UNKNOWN
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    redirect_count: int = 0
    response_time_ms: Optional[float] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    validation_timestamp: datetime
