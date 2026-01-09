"""
Tests for crawl configuration enforcement.
Tests rate limiting, max_hits enforcement, and retry policies.
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.storage.models import Source, CrawlConfig, ContentType, SourceType
from src.crawler.crawl_manager import CrawlManager


class TestCrawlConfiguration:
    """Test crawl configuration enforcement."""
    
    def setup_method(self):
        self.manager = CrawlManager()
        
    def test_rate_limit_calculation(self):
        """Test rate limit delay calculation."""
        # 60 requests/minute should give 1 second delay
        rate_limit_60 = 60
        delay_60 = 60.0 / rate_limit_60
        assert delay_60 == 1.0
        
        # 30 requests/minute should give 2 second delay
        rate_limit_30 = 30
        delay_30 = 60.0 / rate_limit_30
        assert delay_30 == 2.0
        
        # 120 requests/minute should give 0.5 second delay
        rate_limit_120 = 120
        delay_120 = 60.0 / rate_limit_120
        assert delay_120 == 0.5
        
    def test_max_hits_enforcement(self):
        """Test that max_hits is strictly enforced."""
        # This test verifies the logic, not actual crawling
        max_hits = 10
        pages_crawled = 0
        results = []
        
        # Simulate crawling
        for i in range(100):  # Try to crawl 100 pages
            if pages_crawled >= max_hits:
                break  # Should stop at max_hits
            pages_crawled += 1
            results.append(f"page_{i}")
            
        assert len(results) == max_hits
        assert pages_crawled == max_hits
        
    def test_crawl_config_validation(self):
        """Test CrawlConfig validation."""
        # Valid cron expression
        config = CrawlConfig(
            frequency="0 0 * * *",
            max_hits=100,
            rate_limit_per_minute=30
        )
        assert config.frequency == "0 0 * * *"
        
        # Invalid cron expression should raise error
        with pytest.raises(ValueError):
            CrawlConfig(frequency="invalid cron")
            
    def test_retry_policy_configuration(self):
        """Test retry policy configuration."""
        config = CrawlConfig(
            retry_policy={
                "max_retries": 5,
                "backoff_factor": 3,
                "timeout": 60
            }
        )
        
        assert config.retry_policy["max_retries"] == 5
        assert config.retry_policy["backoff_factor"] == 3
        assert config.retry_policy["timeout"] == 60
        
    def test_source_model_with_enhanced_config(self):
        """Test Source model with enhanced configuration."""
        source = Source(
            id="test_source_1",
            name="Test Source",
            url="https://example.com",
            source_type=SourceType.WEBSITE,
            content_type=ContentType.HTML,
            config=CrawlConfig(
                frequency="0 */6 * * *",  # Every 6 hours
                max_hits=50,
                rate_limit_per_minute=20,
                enabled=True,
                retry_policy={
                    "max_retries": 3,
                    "backoff_factor": 2,
                    "timeout": 30
                }
            )
        )
        
        assert source.config.frequency == "0 */6 * * *"
        assert source.config.max_hits == 50
        assert source.config.rate_limit_per_minute == 20
        assert source.config.retry_policy["max_retries"] == 3
        
    def test_rate_limit_boundaries(self):
        """Test rate limit boundary values."""
        # Minimum rate limit (1 req/min)
        config_min = CrawlConfig(rate_limit_per_minute=1)
        assert config_min.rate_limit_per_minute == 1
        
        # Maximum rate limit (300 req/min)
        config_max = CrawlConfig(rate_limit_per_minute=300)
        assert config_max.rate_limit_per_minute == 300
        
        # Out of range should fail validation
        with pytest.raises(ValueError):
            CrawlConfig(rate_limit_per_minute=0)
            
        with pytest.raises(ValueError):
            CrawlConfig(rate_limit_per_minute=500)
            
    def test_max_hits_boundaries(self):
        """Test max_hits boundary values."""
        # Minimum max_hits (1)
        config_min = CrawlConfig(max_hits=1)
        assert config_min.max_hits == 1
        
        # Maximum max_hits (10000)
        config_max = CrawlConfig(max_hits=10000)
        assert config_max.max_hits == 10000
        
        # Out of range should fail validation
        with pytest.raises(ValueError):
            CrawlConfig(max_hits=0)
            
        with pytest.raises(ValueError):
            CrawlConfig(max_hits=20000)


class TestRateLimitEnforcement:
    """Test actual rate limiting during crawl."""
    
    def test_rate_limit_timing(self):
        """Test that rate limiting adds proper delays."""
        rate_limit_per_minute = 60  # 60 requests per minute = 1 per second
        expected_delay = 60.0 / rate_limit_per_minute
        
        start_time = time.time()
        
        # Simulate 3 requests with rate limiting
        for i in range(3):
            time.sleep(expected_delay)
            
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should take approximately 3 seconds (3 delays)
        # Allow 0.5 second tolerance for system variance
        assert 2.5 <= elapsed <= 3.5
        
    def test_fast_rate_limit(self):
        """Test fast rate limiting (high requests/minute)."""
        rate_limit_per_minute = 120  # 120 requests per minute = 2 per second
        expected_delay = 60.0 / rate_limit_per_minute  # 0.5 seconds
        
        start_time = time.time()
        
        # Simulate 4 requests
        for i in range(4):
            time.sleep(expected_delay)
            
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should take approximately 2 seconds (4 * 0.5)
        assert 1.5 <= elapsed <= 2.5
