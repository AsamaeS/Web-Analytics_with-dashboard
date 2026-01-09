"""
Source management API endpoints.
Provides CRUD operations for crawl sources.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..storage import db_manager, Source, CrawlConfig, SourceType, ContentType, CrawlStatus
from ..crawler.scheduler import crawl_scheduler
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# Request/Response models
class SourceCreateRequest(BaseModel):
    """Request model for creating a source."""
    name: str = Field(..., min_length=1, max_length=200)
    url: str
    source_type: SourceType
    content_type: ContentType
    config: Optional[CrawlConfig] = None


class SourceUpdateRequest(BaseModel):
    """Request model for updating a source."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    url: Optional[str] = None
    source_type: Optional[SourceType] = None
    content_type: Optional[ContentType] = None
    config: Optional[CrawlConfig] = None


class SourceResponse(BaseModel):
    """Response model for a source."""
    id: str
    name: str
    url: str
    source_type: SourceType
    content_type: ContentType
    config: CrawlConfig
    status: CrawlStatus
    last_crawl: Optional[str] = None
    last_error: Optional[str] = None
    total_documents: int
    created_at: str
    updated_at: str


# Endpoints
@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(request: SourceCreateRequest):
    """
    Create a new crawl source.
    
    Args:
        request: Source creation request
        
    Returns:
        Created source
    """
    try:
        # Create source object
        source = Source(
            name=request.name,
            url=request.url,
            source_type=request.source_type,
            content_type=request.content_type,
            config=request.config or CrawlConfig()
        )
        
        # Save to database
        source_id = db_manager.create_source(source)
        
        # Schedule if enabled
        if source.config.enabled:
            crawl_scheduler.add_source_job(source_id)
            
        # Get created source
        created_source = db_manager.get_source(source_id)
        
        logger.info(f"Created source: {created_source.name} (ID: {source_id})")
        
        return _source_to_response(created_source)
        
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    status_filter: Optional[CrawlStatus] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all sources with optional filtering.
    
    Args:
        status_filter: Filter by crawl status
        limit: Maximum number of results
        offset: Number of results to skip
        
    Returns:
        List of sources
    """
    try:
        sources = db_manager.list_sources(
            status=status_filter,
            limit=limit,
            offset=offset
        )
        
        return [_source_to_response(source) for source in sources]
        
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str):
    """
    Get source by ID.
    
    Args:
        source_id: Source ID
        
    Returns:
        Source details
    """
    source = db_manager.get_source(source_id)
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    return _source_to_response(source)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: str, request: SourceUpdateRequest):
    """
    Update source configuration.
    
    Args:
        source_id: Source ID
        request: Update request
        
    Returns:
        Updated source
    """
    # Check if source exists
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    try:
        # Build update dictionary
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.url is not None:
            updates["url"] = request.url
        if request.source_type is not None:
            updates["source_type"] = request.source_type.value
        if request.content_type is not None:
            updates["content_type"] = request.content_type.value
        if request.config is not None:
            updates["config"] = request.config.model_dump()
            
        # Update in database
        db_manager.update_source(source_id, updates)
        
        # Update scheduler if config changed
        if request.config is not None:
            if request.config.enabled:
                crawl_scheduler.add_source_job(source_id)
            else:
                crawl_scheduler.remove_source_job(source_id)
                
        # Get updated source
        updated_source = db_manager.get_source(source_id)
        
        logger.info(f"Updated source: {source_id}")
        
        return _source_to_response(updated_source)
        
    except Exception as e:
        logger.error(f"Failed to update source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str):
    """
    Delete source and all its documents.
    
    Args:
        source_id: Source ID
    """
    # Check if source exists
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    try:
        # Remove from scheduler
        crawl_scheduler.remove_source_job(source_id)
        
        # Delete from database
        db_manager.delete_source(source_id)
        
        logger.info(f"Deleted source: {source_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Helper functions
def _source_to_response(source: Source) -> SourceResponse:
    """Convert Source model to response."""
    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        source_type=source.source_type,
        content_type=source.content_type,
        config=source.config,
        status=source.status,
        last_crawl=source.last_crawl.isoformat() if source.last_crawl else None,
        last_error=source.last_error,
        total_documents=source.total_documents,
        created_at=source.created_at.isoformat(),
        updated_at=source.updated_at.isoformat()
    )
