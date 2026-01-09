"""
Scheduler for automated crawling using APScheduler.
Manages per-source cron schedules and prevents overlapping crawls.
"""

from typing import Dict, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

from .crawl_manager import CrawlManager
from ..storage import db_manager, CrawlStatus
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CrawlScheduler:
    """Manages scheduled crawling jobs."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawl_manager = CrawlManager()
        self.active_crawls: Dict[str, bool] = {}  # Track active crawls per source
        self.logger = setup_logger(self.__class__.__name__)
        
    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Crawler scheduler started")
            
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.
        
        Args:
            wait: Whether to wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            self.crawl_manager.close()
            self.logger.info("Crawler scheduler shut down")
            
    def add_source_job(self, source_id: str) -> bool:
        """
        Add or update a scheduled job for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if job was added/updated successfully
        """
        try:
            # Get source configuration
            source = db_manager.get_source(source_id)
            if not source:
                self.logger.error(f"Source not found: {source_id}")
                return False
                
            if not source.config.enabled:
                self.logger.info(f"Source {source.name} is disabled, not scheduling")
                return False
                
            # Remove existing job if any
            self.remove_source_job(source_id)
            
            # Parse cron expression
            cron_parts = source.config.frequency.split()
            if len(cron_parts) != 5:
                self.logger.error(f"Invalid cron expression for {source.name}: {source.config.frequency}")
                return False
                
            minute, hour, day, month, day_of_week = cron_parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job
            job_id = f"crawl_{source_id}"
            self.scheduler.add_job(
                func=self._crawl_job,
                trigger=trigger,
                args=[source_id],
                id=job_id,
                name=f"Crawl: {source.name}",
                replace_existing=True,
                misfire_grace_time=3600  # Allow 1 hour grace period
            )
            
            self.logger.info(f"Scheduled crawl job for {source.name} with cron: {source.config.frequency}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add job for source {source_id}: {e}")
            return False
            
    def remove_source_job(self, source_id: str) -> bool:
        """
        Remove scheduled job for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if job was removed
        """
        try:
            job_id = f"crawl_{source_id}"
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed scheduled job: {job_id}")
            return True
        except JobLookupError:
            # Job doesn't exist, that's fine
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove job {job_id}: {e}")
            return False
            
    def pause_source_job(self, source_id: str) -> bool:
        """
        Pause scheduled job for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if job was paused
        """
        try:
            job_id = f"crawl_{source_id}"
            self.scheduler.pause_job(job_id)
            db_manager.update_source(source_id, {"status": CrawlStatus.PAUSED.value})
            self.logger.info(f"Paused job: {job_id}")
            return True
        except JobLookupError:
            self.logger.warning(f"Job not found: {job_id}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause job {job_id}: {e}")
            return False
            
    def resume_source_job(self, source_id: str) -> bool:
        """
        Resume paused job for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if job was resumed
        """
        try:
            job_id = f"crawl_{source_id}"
            self.scheduler.resume_job(job_id)
            db_manager.update_source(source_id, {"status": CrawlStatus.IDLE.value})
            self.logger.info(f"Resumed job: {job_id}")
            return True
        except JobLookupError:
            self.logger.warning(f"Job not found: {job_id}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume job {job_id}: {e}")
            return False
            
    def trigger_source_crawl(self, source_id: str) -> bool:
        """
        Manually trigger a crawl for a source (outside of schedule).
        
        Args:
            source_id: Source ID
            
        Returns:
            True if crawl was triggered
        """
        # Check if crawl is already running
        if self.active_crawls.get(source_id, False):
            self.logger.warning(f"Crawl already running for source {source_id}")
            return False
            
        # Run in background thread
        self.scheduler.add_job(
            func=self._crawl_job,
            args=[source_id],
            id=f"manual_crawl_{source_id}_{datetime.utcnow().timestamp()}",
            name=f"Manual crawl: {source_id}"
        )
        
        self.logger.info(f"Triggered manual crawl for source {source_id}")
        return True
        
    def _crawl_job(self, source_id: str) -> None:
        """
        Execute crawl job for a source.
        Prevents overlapping crawls for the same source.
        
        Args:
            source_id: Source ID
        """
        # Check if already crawling this source
        if self.active_crawls.get(source_id, False):
            self.logger.warning(f"Skipping crawl for {source_id} - already in progress")
            return
            
        try:
            self.active_crawls[source_id] = True
            self.logger.info(f"Starting scheduled crawl for source {source_id}")
            self._execute_crawl(source_id)
            
        except Exception as e:
            self.logger.error(f"Scheduled crawl failed for {source_id}: {e}")
            self.active_crawls[source_id] = False # Ensure cleanup if _execute_crawl itself fails to start
            
    def _execute_crawl(self, source_id: str):
        """
        Execute crawl job (synchronous wrapper for async crawl).
        
        Args:
            source_id: Source ID to crawl
        """
        import asyncio
        import traceback
        
        try:
            self.logger.info(f"Executing scheduled crawl for source: {source_id}")
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run async crawl_source in the new loop
                # Use self.crawl_manager as it's already initialized
                stats = loop.run_until_complete(self.crawl_manager.crawl_source(source_id))
                
                self.logger.info(
                    f"Scheduled crawl completed for {source_id}: "
                    f"{stats.pages_crawled} pages, {stats.pages_failed} failed"
                )
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Scheduled crawl failed for {source_id}: {e}")
            self.logger.error(traceback.format_exc())
            
        finally:
            self.active_crawls[source_id] = False
            
    def load_all_sources(self) -> int:
        """
        Load and schedule all enabled sources from database.
        
        Returns:
            Number of sources scheduled
        """
        try:
            sources = db_manager.list_sources()
            scheduled_count = 0
            
            for source in sources:
                if source.config.enabled:
                    if self.add_source_job(source.id):
                        scheduled_count += 1
                        
            self.logger.info(f"Loaded {scheduled_count} scheduled crawl jobs")
            return scheduled_count
            
        except Exception as e:
            self.logger.error(f"Failed to load sources: {e}")
            return 0
            
    def get_job_info(self, source_id: str) -> Optional[dict]:
        """
        Get information about a scheduled job.
        
        Args:
            source_id: Source ID
            
        Returns:
            Job info dictionary or None if not found
        """
        try:
            job_id = f"crawl_{source_id}"
            job = self.scheduler.get_job(job_id)
            
            if job:
                return {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time,
                    "trigger": str(job.trigger)
                }
        except JobLookupError:
            pass
            
        return None
        
    def list_jobs(self) -> list:
        """
        List all scheduled jobs.
        
        Returns:
            List of job info dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return jobs


# Global scheduler instance
crawl_scheduler = CrawlScheduler()
