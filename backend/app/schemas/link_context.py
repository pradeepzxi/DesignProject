"""Link Context Schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class LinkContextBase(BaseModel):
    anchor_text: Optional[str] = None
    surrounding_text: Optional[str] = None
    paragraph_text: Optional[str] = None
    section_heading: Optional[str] = None
    document_title: Optional[str] = None
    url_tokens: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None


class LinkContextResponse(LinkContextBase):
    context_id: str
    link_id: str

    model_config = ConfigDict(from_attributes=True)
