"""
Data models for the web crawler application.
Defines Pydantic models for sources and documents with validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ContentType(str, Enum):
    """Supported content types for crawling."""
    HTML = "html"
    RSS = "rss"
    PDF = "pdf"
    TXT = "txt"
    TWITTER = "twitter"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"


class CrawlStatus(str, Enum):
    """Crawl job status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    BLOCKED = "blocked"  # For HTTP 403/429, CAPTCHA, or IP ban


class SourceType(str, Enum):
    """Types of sources that can be crawled."""
    WEBSITE = "website"
    BLOG = "blog"
    RSS_FEED = "rss_feed"
    DOCUMENT = "document"
    API = "api"
    TWITTER = "twitter"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"


class CrawlConfig(BaseModel):
    """Crawl configuration model."""
    
    frequency: str = Field(
        default="0 0 * * *",  # Daily at midnight
        description="Cron expression for scheduling"
    )
    max_hits: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum pages to crawl"
    )
    enabled: bool = Field(
        default=True,
        description="Enable/disable crawling"
    )
    follow_links: bool = Field(
        default=False,
        description="Follow links on pages"
    )
    max_depth: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum crawl depth"
    )
    rate_limit_per_minute: int = Field(default=30, ge=1, le=300, description="Maximum requests per minute")
    retry_policy: Dict[str, int] = Field(
        default={"max_retries": 3, "backoff_factor": 2, "timeout": 30},
        description="Retry policy configuration"
    )
    
    @field_validator("frequency")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Validate cron expression."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                "Cron expression must have 5 parts: minute hour day month weekday"
            )
        return v


class Project(BaseModel):
    """Project model for grouping sources and defining analysis scope."""
    
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier (MongoDB ObjectId as string)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Project name (e.g., 'Healthcare Investment Analysis')"
    )
    domain: str = Field(
        ...,
        description="Business domain (e.g., 'Healthcare', 'Finance', 'Energy')"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Target keywords for this project"
    )
    description: Optional[str] = Field(
        default=None,
        description="Project description or objective"
    )
    icon: str = Field(
        default="📊",
        description="Emoji icon for UI display"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when project was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when project was last updated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Healthcare Investment Analysis",
                "domain": "Healthcare",
                "keywords": ["hospital", "medical", "healthcare policy", "regulation"],
                "description": "Investment opportunity analysis in healthcare sector",
                "icon": "🏥"
            }
        }


class Source(BaseModel):
    """Source configuration for web crawling."""
    
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier (MongoDB ObjectId as string)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable name for the source"
    )
    url: str = Field(
        ...,
        description="Source URL to crawl"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Reference to project (ObjectId as string)"
    )
    source_type: SourceType = Field(
        ...,
        description="Type of source (website, blog, RSS feed, etc.)"
    )
    content_type: ContentType = Field(
        ...,
        description="Expected content type (html, rss, pdf, txt)"
    )
    config: CrawlConfig = Field(
        default_factory=CrawlConfig,
        description="Crawl configuration settings"
    )
    status: CrawlStatus = Field(
        default=CrawlStatus.IDLE,
        description="Current crawl status"
    )
    last_crawl: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last successful crawl"
    )
    last_error: Optional[str] = Field(
        default=None,
        description="Last error message if crawl failed"
    )
    total_documents: int = Field(
        default=0,
        ge=0,
        description="Total number of documents collected from this source"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when source was added"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when source was last updated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tech Blog",
                "url": "https://example.com/blog",
                "source_type": "blog",
                "content_type": "html",
                "config": {
                    "frequency": "0 8 * * *",
                    "max_hits": 50,
                    "enabled": True
                }
            }
        }


class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""
    
    title: Optional[str] = Field(
        default=None,
        description="Document title"
    )
    author: Optional[str] = Field(
        default=None,
        description="Document author"
    )
    publish_date: Optional[datetime] = Field(
        default=None,
        description="Publication date"
    )
    language: Optional[str] = Field(
        default=None,
        description="Document language (ISO code)"
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Word count of cleaned text"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Extracted keywords"
    )
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )


class Document(BaseModel):
    """Document collected by the crawler."""
    
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier (MongoDB ObjectId as string)"
    )
    url: str = Field(
        ...,
        description="Document URL"
    )
    source_id: str = Field(
        ...,
        description="Reference to source (ObjectId as string)"
    )
    content_type: ContentType = Field(
        ...,
        description="Content type of the document"
    )
    raw_content: str = Field(
        ...,
        description="Raw content as retrieved"
    )
    cleaned_text: str = Field(
        ...,
        description="Cleaned and processed text for searching"
    )
    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata,
        description="Document metadata"
    )
    crawl_config_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Snapshot of crawl configuration at collection time"
    )
    crawled_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when document was crawled"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/blog/article",
                "source_id": "507f1f77bcf86cd799439011",
                "content_type": "html",
                "raw_content": "<html>...</html>",
                "cleaned_text": "Article content here...",
                "metadata": {
                    "title": "Example Article",
                    "word_count": 150,
                    "keywords": ["example", "article", "content"]
                }
            }
        }


class CrawlStats(BaseModel):
    """Statistics for a crawl run."""
    
    source_id: str
    pages_crawled: int = 0
    pages_failed: int = 0
    bytes_downloaded: int = 0
    duration_seconds: float = 0.0
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    """Search query parameters."""
    
    keywords: str = Field(
        ...,
        min_length=1,
        description="Keywords to search for"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Filter by source ID"
    )
    content_type: Optional[ContentType] = Field(
        default=None,
        description="Filter by content type"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter documents from this date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter documents until this date"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip (for pagination)"
    )


class SearchResult(BaseModel):
    """Search result item."""
    
    document_id: str
    url: str
    title: Optional[str]
    snippet: str
    relevance_score: float
    source_id: str
    content_type: ContentType
    crawled_at: datetime
