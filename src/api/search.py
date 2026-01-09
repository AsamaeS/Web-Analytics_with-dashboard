"""
Search API endpoints.
Provides keyword-based search functionality.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..storage import ContentType, SearchResult
from ..processing.search import search_engine
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# Response models
class SearchResultResponse(BaseModel):
    """Response model for a search result."""
    document_id: str
    url: str
    title: Optional[str]
    snippet: str
    relevance_score: float
    source_id: str
    content_type: str
    crawled_at: str


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    total_results: int
    results: List[SearchResultResponse]
    limit: int
    offset: int


# Endpoints
@router.get("/", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search keywords"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    date_from: Optional[datetime] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset for pagination"),
    operator: str = Query("AND", pattern="^(AND|OR)$", description="Boolean operator")
):
    """
    Search documents using keyword-based full-text search.
    
    Args:
        q: Search keywords
        source_id: Optional source filter
        content_type: Optional content type filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        limit: Maximum number of results
        offset: Results offset for pagination
        operator: Boolean operator (AND or OR)
        
    Returns:
        Search results with metadata
    """
    try:
        # Execute search
        if operator == "OR":
            results = search_engine.search_with_boolean(
                keywords=q,
                operator="OR",
                source_id=source_id,
                content_type=content_type,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
        else:
            results = search_engine.search(
                keywords=q,
                source_id=source_id,
                content_type=content_type,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
            
        # Convert to response models
        result_responses = [
            SearchResultResponse(
                document_id=r.document_id,
                url=r.url,
                title=r.title,
                snippet=r.snippet,
                relevance_score=r.relevance_score,
                source_id=r.source_id,
                content_type=r.content_type.value,
                crawled_at=r.crawled_at.isoformat()
            )
            for r in results
        ]
        
        return SearchResponse(
            query=q,
            total_results=len(result_responses),
            results=result_responses,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions")
):
    """
    Get search suggestions based on existing keywords.
    
    Args:
        q: Partial query
        limit: Maximum suggestions
        
    Returns:
        List of suggestions
    """
    # Simple implementation: return empty for now
    # In production, this could use a keyword index or autocomplete
    return {
        "query": q,
        "suggestions": []
    }
