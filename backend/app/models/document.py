from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    """Document source types - extensible for future formats."""
    WEB_ARTICLE = "web_article"
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    UPLOAD = "upload"


class DocumentBase(BaseModel):
    """Base document fields for creation."""
    url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    """Fields required when creating a document."""
    html_content: str  # Raw HTML to be parsed
    source_type: SourceType = SourceType.WEB_ARTICLE


class DocumentUpdate(BaseModel):
    """Fields that can be updated."""
    title: Optional[str] = None
    tags: Optional[list[str]] = None
    read_status: Optional[bool] = None


class Document(DocumentBase):
    """Full document model with all fields."""
    id: UUID = Field(default_factory=uuid4)
    source_type: SourceType = SourceType.WEB_ARTICLE
    content: str = ""  # Extracted plain text
    summary: str = ""  # LLM-generated summary
    read_status: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class DocumentResponse(Document):
    """Document response with optional computed fields."""
    relevance_score: Optional[float] = None  # For search results


class SearchRequest(BaseModel):
    """Search query parameters."""
    query: str
    semantic: bool = True  # Use semantic search
    tags: Optional[list[str]] = None
    read_status: Optional[bool] = None
    limit: int = 20
    offset: int = 0


class SearchResponse(BaseModel):
    """Search results."""
    results: list[DocumentResponse]
    total: int
    query: str
