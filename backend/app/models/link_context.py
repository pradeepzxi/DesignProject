"""Link Context Model.

Stores rich linguistic, syntactic, and structural context surrounding an extracted
hyperlink for research classification and downstream semantic candidate retrieval.
"""

import uuid
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class LinkContext(Base):
    __tablename__ = "link_context"

    context_id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    link_id = Column(
        String(36),
        ForeignKey("links.link_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    anchor_text = Column(Text, nullable=True)
    surrounding_text = Column(Text, nullable=True)
    paragraph_text = Column(Text, nullable=True)
    section_heading = Column(Text, nullable=True)
    document_title = Column(Text, nullable=True)
    # url_tokens: stores JSON list/dict of parsed path, domain, filename, query tokens
    url_tokens = Column(JSON, nullable=True)
    # keywords: stores list of salient domain keywords extracted from surrounding context
    keywords = Column(JSON, nullable=True)

    # Relationship
    link = relationship("Link", back_populates="context")
