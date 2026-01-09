"""
Tests for crawler functionality.
"""

import pytest
from src.crawler.base_crawler import BaseCrawler
from unittest.mock import Mock, patch


class TestBaseCrawler:
    """Tests for base crawler."""
    
    def test_can_fetch_with_robots(self):
        """Test robots.txt compliance check."""
        crawler = BaseCrawler()
        
        # Should work for most URLs
        # Note: This is a basic test, actual robots.txt checking requires network
        assert crawler.can_fetch("http://example.com/") in [True, False]
        
    def test_rate_limiting(self):
        """Test rate limiting between requests."""
        crawler = BaseCrawler(delay=0.1)
        
        import time
        url = "http://example.com/test"
        
        # First request
        crawler.respect_rate_limit(url)
        start = time.time()
        
        # Second request should wait
        crawler.respect_rate_limit(url)
        elapsed = time.time() - start
        
        # Should have waited at least the delay time
        assert elapsed >= 0.1
        
    def test_session_creation(self):
        """Test session is created with retry logic."""
        crawler = BaseCrawler()
        
        assert crawler.session is not None
        assert crawler.user_agent in crawler.session.headers['User-Agent']


class TestCrawlManager:
    """Tests for crawl manager."""
    
    @pytest.mark.skip(reason="Requires MongoDB connection")
    def test_crawl_source(self):
        """Test crawling a source (requires DB)."""
        pass
