"""
Crawl orchestration manager.
Manages crawling workflow for individual sources with blocking detection and rate limiting.
"""

from typing import Optional, List
from datetime import datetime
import time
from bson import ObjectId

from ..storage import db_manager, Source, Document, CrawlStatus, ContentType, CrawlStats, DocumentMetadata
from ..utils.logger import setup_logger
from .base_crawler import BaseCrawler
from .parsers import (
    HTMLParser, RSSParser, PDFParser, TXTParser, ParserResult,
    TwitterParser, RedditParser, YouTubeParser, LinkedInParser
)
from .blocking_detector import blocking_detector

logger = setup_logger(__name__)


class CrawlManager:
    """Manages the crawling process for a source with advanced features."""
    
    def __init__(self):
        self.crawler = BaseCrawler()
        self.parsers = {
            ContentType.HTML: HTMLParser(),
            ContentType.RSS: RSSParser(),
            ContentType.PDF: PDFParser(),
            ContentType.TXT: TXTParser(),
            ContentType.TWITTER: TwitterParser(),
            ContentType.REDDIT: RedditParser(),
            ContentType.YOUTUBE: YouTubeParser(),
            ContentType.LINKEDIN: LinkedInParser(),
        }
        
    async def crawl_source(self, source_id: str) -> CrawlStats:
        """
        Crawl a source with blocking detection and rate limiting.
        
        Args:
            source_id: Source ID
            
        Returns:
            CrawlStats object
        """
        # Get source
        source = db_manager.get_source(source_id)
        if not source:
            raise ValueError(f"Source not found: {source_id}")
            
        logger.info(f"Starting crawl for source: {source.name} ({source_id})")
        
        # Initialize stats
        stats = CrawlStats(
            source_id=source_id,
            source_name=source.name,
            started_at=datetime.utcnow()
        )
        
        # Update source status
        db_manager.update_source(source_id, {
            "status": CrawlStatus.RUNNING.value,
            "last_crawl": datetime.utcnow()
        })
        
        try:
            # Calculate rate limit delay (convert requests/minute to delay in seconds)
            rate_limit_delay = 60.0 / source.config.rate_limit_per_minute
            
            # Crawl based on content type
            if source.content_type in [ContentType.TWITTER, ContentType.REDDIT, ContentType.YOUTUBE]:
                # Social media sources use API methods
                results = self._crawl_social_media(source, stats)
            else:
                # Traditional web crawling
                results = self._crawl_traditional(source, stats, rate_limit_delay)
                
            # Store results
            documents_stored = 0
            for result in results:
                if stats.pages_crawled >= source.config.max_hits:
                    logger.info(f"Reached max_hits limit ({source.config.max_hits})")
                    break
                    
                try:
                    self._store_document(source, result)
                    documents_stored += 1
                    stats.pages_crawled += 1
                    
                    # Rate limiting
                    time.sleep(rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Failed to store document: {e}")
                    stats.pages_failed += 1
                    stats.errors.append(str(e))
                    
            # Update stats
            stats.completed_at = datetime.utcnow()
            stats.duration_seconds = (stats.completed_at - stats.started_at).total_seconds()
            
            # Update source
            db_manager.update_source(source_id, {
                "status": CrawlStatus.COMPLETED.value,
                "total_documents": source.total_documents + documents_stored,
                "last_error": None
            })
            
            # Save stats
            db_manager.save_crawl_stats(stats)
            
            logger.info(
                f"Crawl completed for {source.name}: "
                f"{stats.pages_crawled} pages, {stats.pages_failed} failed, "
                f"{stats.duration_seconds:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Crawl failed for {source.name}: {e}")
            stats.completed_at = datetime.utcnow()
            stats.errors.append(str(e))
            
            # Update source status
            db_manager.update_source(source_id, {
                "status": CrawlStatus.FAILED.value,
                "last_error": str(e)
            })
            
        return stats
        
    def _crawl_traditional(self, source: Source, stats: CrawlStats, rate_limit_delay: float) -> List[ParserResult]:
        """Crawl traditional web sources with blocking detection."""
        results = []
        urls_to_crawl = [source.url]
        crawled_urls = set()
        
        while urls_to_crawl and len(results) < source.config.max_hits:
            url = urls_to_crawl.pop(0)
            
            if url in crawled_urls:
                continue
                
            try:
                # Fetch content
                response = self.crawler.fetch(url)
                
                if not response:
                    stats.pages_failed += 1
                    continue
                    
                # Blocking detection
                block_result = blocking_detector.detect_all(
                    response.content,
                    response.status_code,
                    url
                )
                
                if block_result["blocked"]:
                    logger.error(
                        f"Blocking detected: {block_result['block_type']} - "
                        f"Pausing source {source.name}"
                    )
                    
                    # Update to BLOCKED status
                    db_manager.update_source(source.id, {
                        "status": CrawlStatus.BLOCKED.value,
                        "last_error": f"Blocked: {block_result['block_type']}"
                    })
                    
                    stats.errors.append(f"Blocked: {block_result['block_type']}")
                    break
                    
                # Parse content
                parser = self.parsers.get(source.content_type)
                if not parser:
                    raise ValueError(f"No parser for content type: {source.content_type}")
                    
                result = parser.parse(response.content, url)
                results.append(result)
                crawled_urls.add(url)
                
                stats.bytes_downloaded += len(response.content)
                
                # Follow links if enabled
                if source.config.follow_links and hasattr(result, 'next_page') and result.next_page:
                    if result.next_page not in crawled_urls:
                        urls_to_crawl.append(result.next_page)
                        
                # Rate limiting
                time.sleep(rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                stats.pages_failed += 1
                stats.errors.append(f"{url}: {str(e)}")
                
        return results
        
    def _crawl_social_media(self, source: Source, stats: CrawlStats) -> List[ParserResult]:
        """
        Crawl social media sources (Twitter, Reddit, YouTube, LinkedIn).
        
        Args:
            source: Source configuration
            stats: Statistics tracker
            
        Returns:
            List of parser results
        """
        results = []
        
        try:
            # Get appropriate parser
            parser = self.parsers.get(source.content_type)
            if not parser:
                raise ValueError(f"No parser for social platform: {source.content_type}")
                
            logger.info(f"Crawling social media: {source.content_type.value} - {source.url}")
            
            # Fetch content (social parsers handle API calls internally)
            response = self.crawler.fetch(source.url)
            
            if not response:
                stats.pages_failed += 1
                return results
                
            stats.bytes_downloaded += len(response.content) if response.content else 0
            
            # Parse based on platform
            if source.content_type == ContentType.TWITTER:
                # Twitter parser extracts tweets
                result = parser.parse(response.content, source.url)
                if result:
                    results.append(result)
                    
            elif source.content_type == ContentType.REDDIT:
                # Reddit parser extracts posts
                result = parser.parse({}, source.url)  # Reddit parser uses URL directly
                if result and hasattr(result, 'items'):
                    results.extend(result.items[:source.config.max_hits])
                elif result:
                    results.append(result)
                    
            elif source.content_type == ContentType.YOUTUBE:
                # YouTube parser extracts videos from RSS
                result = parser.parse(response.content, source.url)
                if result and hasattr(result, 'items'):
                    results.extend(result.items[:source.config.max_hits])
                elif result:
                    results.append(result)
                    
            elif source.content_type == ContentType.LINKEDIN:
                # LinkedIn parser extracts company posts
                result = parser.parse(response.content, source.url)
                if result:
                    results.append(result)
                    
            logger.info(f"Social media crawl extracted {len(results)} items")
            
        except Exception as e:
            logger.error(f"Social media crawl failed for {source.url}: {e}")
            stats.pages_failed += 1
            stats.errors.append(f"Social media error: {str(e)}")
            
        return results[:source.config.max_hits]
        
    def _store_document(self, source: Source, result: ParserResult) -> None:
        """
        Store a single document from parser result.
        
        Args:
            source: Source configuration
            result: Parser result
        """
        try:
            # Convert ParserResult to Document
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else {
                'url': result.url if hasattr(result, 'url') else source.url,
                'content_type': source.content_type.value,
                'raw_content': result.raw_content if hasattr(result, 'raw_content') else '',
                'cleaned_text': result.cleaned_text if hasattr(result, 'cleaned_text') else result.text,
                'metadata': result.metadata if hasattr(result, 'metadata') else {}
            }
            
            # Create document
            document = Document(
                url=result_dict.get('url', source.url),
                source_id=source.id,
                content_type=source.content_type,
                raw_content=result_dict.get('raw_content', ''),
                cleaned_text=result_dict.get('cleaned_text', ''),
                metadata=DocumentMetadata(**result_dict.get('metadata', {})),
                crawl_config_snapshot=source.config.dict()
            )
            
            # Store in database
            doc_id = db_manager.create_document(document)
            if doc_id:
                logger.debug(f"Stored document: {document.url}")
            else:
                logger.debug(f"Document already exists: {document.url}")
                
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise
        
    def _crawl_rss(self, source: Source, stats: CrawlStats) -> List[ParserResult]:
        """
        Crawl RSS feed.
        
        Args:
            source: Source configuration
            stats: Statistics tracker
            
        Returns:
            List of parser results (one per entry)
        """
        try:
            # Fetch feed
            content = self.crawler.fetch(source.url)
            if not content:
                stats.pages_failed += 1
                raise ValueError("Failed to fetch RSS feed")
                
            stats.bytes_downloaded += len(content)
            
            # Parse feed entries
            parser = self.parsers[ContentType.RSS]
            results = parser.parse_entries(content, source.url)
            
            # Limit to max_hits
            max_hits = source.config.max_hits
            results = results[:max_hits]
            
            stats.pages_crawled = len(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to crawl RSS feed {source.url}: {e}")
            stats.pages_failed += 1
            stats.errors.append(str(e))
            raise
            
    def _store_results(
        self,
        source_id: str,
        config_snapshot: dict,
        results: List[ParserResult],
        stats: CrawlStats
    ) -> None:
        """
        Store parsed results in database.
        
        Args:
            source_id: Source ID
            config_snapshot: Snapshot of crawl configuration
            results: List of parser results
            stats: Statistics tracker
        """
        for result in results:
            try:
                # Convert ParserResult to Document
                result_dict = result.to_dict()
                
                document = Document(
                    url=result_dict["url"],
                    source_id=source_id,
                    content_type=result_dict["content_type"],
                    raw_content=result_dict["raw_content"],
                    cleaned_text=result_dict["cleaned_text"],
                    metadata=DocumentMetadata(**result_dict["metadata"]),
                    crawl_config_snapshot=config_snapshot
                )
                
                # Store in database
                doc_id = db_manager.create_document(document)
                if doc_id:
                    self.logger.debug(f"Stored document: {document.url}")
                else:
                    self.logger.debug(f"Document already exists: {document.url}")
                    
            except Exception as e:
                self.logger.error(f"Failed to store document {result.url}: {e}")
                stats.errors.append(f"Storage error for {result.url}: {str(e)}")
                
        # Update source document count
        total_docs = db_manager.count_documents(source_id)
        db_manager.update_source(source_id, {"total_documents": total_docs})
        
    def close(self) -> None:
        """Close crawler resources."""
        self.crawler.close()
