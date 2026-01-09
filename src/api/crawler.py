"""
Crawler control API endpoints.
Provides endpoints to start, stop, and monitor crawls.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from ..storage import db_manager, CrawlStatus
from ..crawler.scheduler import crawl_scheduler
from ..crawler.crawl_manager import CrawlManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# Response models
class CrawlStatusResponse(BaseModel):
    """Response model for crawl status."""
    source_id: str
    status: CrawlStatus
    scheduled: bool
    next_run_time: Optional[str] = None
    last_crawl: Optional[str] = None
    total_documents: int


class CrawlStatsResponse(BaseModel):
    """Response model for crawl statistics."""
    total_sources: int
    total_documents: int
    active_crawls: int
    scheduled_jobs: int


class CrawlTriggerResponse(BaseModel):
    """Response model for triggering a crawl."""
    message: str
    source_id: str


# Endpoints
@router.post("/start/{source_id}", response_model=CrawlTriggerResponse)
async def start_crawl(source_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger a crawl for a source.
    
    Args:
        source_id: Source ID
        background_tasks: FastAPI background tasks
        
    Returns:
        Trigger confirmation
    """
    # Check if source exists
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    # Check if already running
    if source.status == CrawlStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Crawl already running for source: {source_id}"
        )
        
    try:
        # Trigger crawl
        success = crawl_scheduler.trigger_source_crawl(source_id)
        
        if success:
            logger.info(f"Triggered manual crawl for source: {source_id}")
            return CrawlTriggerResponse(
                message="Crawl started",
                source_id=source_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to trigger crawl"
            )
            
    except Exception as e:
        logger.error(f"Failed to start crawl for {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop/{source_id}")
async def stop_crawl(source_id: str):
    """
    Stop/pause scheduled crawling for a source.
    
    Args:
        source_id: Source ID
        
    Returns:
        Stop confirmation
    """
    # Check if source exists
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    try:
        # Pause the job
        success = crawl_scheduler.pause_source_job(source_id)
        
        if success:
            logger.info(f"Paused crawl job for source: {source_id}")
            return {"message": "Crawl job paused", "source_id": source_id}
        else:
            # Job might not exist
            return {"message": "No active job for source", "source_id": source_id}
            
    except Exception as e:
        logger.error(f"Failed to stop crawl for {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/resume/{source_id}")
async def resume_crawl(source_id: str):
    """
    Resume paused crawling for a source.
    
    Args:
        source_id: Source ID
        
    Returns:
        Resume confirmation
    """
    # Check if source exists
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    try:
        # Resume the job
        success = crawl_scheduler.resume_source_job(source_id)
        
        if success:
            logger.info(f"Resumed crawl job for source: {source_id}")
            return {"message": "Crawl job resumed", "source_id": source_id}
        else:
            # Job might not exist, try to add it
            crawl_scheduler.add_source_job(source_id)
            return {"message": "Crawl job scheduled", "source_id": source_id}
            
    except Exception as e:
        logger.error(f"Failed to resume crawl for {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status/{source_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(source_id: str):
    """
    Get crawl status for a source.
    
    Args:
        source_id: Source ID
        
    Returns:
        Crawl status information
    """
    # Get source
    source = db_manager.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source not found: {source_id}"
        )
        
    # Get job info
    job_info = crawl_scheduler.get_job_info(source_id)
    
    return CrawlStatusResponse(
        source_id=source_id,
        status=source.status,
        scheduled=job_info is not None,
        next_run_time=job_info["next_run_time"].isoformat() if job_info and job_info["next_run_time"] else None,
        last_crawl=source.last_crawl.isoformat() if source.last_crawl else None,
        total_documents=source.total_documents
    )


@router.get("/stats", response_model=CrawlStatsResponse)
async def get_crawl_stats():
    """
    Get global crawl statistics.
    
    Returns:
        Global statistics
    """
    try:
        # Get stats from database
        stats = db_manager.get_global_stats()
        
        # Get scheduler info
        jobs = crawl_scheduler.list_jobs()
        
        # Count active crawls
        sources = db_manager.list_sources()
        active_crawls = sum(1 for s in sources if s.status == CrawlStatus.RUNNING)
        
        return CrawlStatsResponse(
            total_sources=stats["total_sources"],
            total_documents=stats["total_documents"],
            active_crawls=active_crawls,
            scheduled_jobs=len(jobs)
        )
        
    except Exception as e:
        logger.error(f"Failed to get crawl stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs")
async def list_scheduled_jobs():
    """
    List all scheduled crawl jobs.
    
    Returns:
        List of scheduled jobs
    """
    try:
        jobs = crawl_scheduler.list_jobs()
        return {"jobs": jobs, "count": len(jobs)}
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
