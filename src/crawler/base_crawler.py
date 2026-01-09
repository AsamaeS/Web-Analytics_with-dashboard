"""
Base crawler with politeness rules, robots.txt compliance, and retry logic.
Provides foundation for crawling web sources responsibly.
"""

from typing import Optional
import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import setup_logger
from ..utils.config import settings

logger = setup_logger(__name__)


class BaseCrawler:
    """Base crawler with politeness and retry logic."""
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay: float = None,
        max_retries: int = None,
        timeout: int = None
    ):
        """
        Initialize crawler.
        
        Args:
            user_agent: Custom user agent (defaults to settings)
            delay: Delay between requests in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.user_agent = user_agent or settings.crawler_user_agent
        self.delay = delay if delay is not None else settings.crawler_delay
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.timeout = timeout if timeout is not None else settings.request_timeout
        
        self.session = self._create_session()
        self.robots_cache = {}  # Cache robots.txt parsers per domain
        self.last_request_time = {}  # Track last request time per domain
        
        self.logger = setup_logger(self.__class__.__name__)
        
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Exponential backoff: {backoff factor} * (2 ** (retry_count - 1))
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': self.user_agent
        })
        
        return session
        
    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if fetching is allowed, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Get or create robots.txt parser for this domain
            if domain not in self.robots_cache:
                robot_parser = RobotFileParser()
                robot_url = urljoin(domain, '/robots.txt')
                
                try:
                    robot_parser.set_url(robot_url)
                    robot_parser.read()
                    self.robots_cache[domain] = robot_parser
                    self.logger.debug(f"Loaded robots.txt from {robot_url}")
                except Exception as e:
                    # If robots.txt cannot be fetched, assume crawling is allowed
                    self.logger.warning(f"Failed to fetch robots.txt from {robot_url}: {e}")
                    self.robots_cache[domain] = None
                    
            robot_parser = self.robots_cache.get(domain)
            
            if robot_parser is None:
                # No robots.txt, allow crawling
                return True
                
            return robot_parser.can_fetch(self.user_agent, url)
            
        except Exception as e:
            self.logger.error(f"Error checking robots.txt for {url}: {e}")
            # On error, allow crawling
            return True
            
    def respect_rate_limit(self, url: str) -> None:
        """
        Enforce rate limiting by waiting if necessary.
        
        Args:
            url: URL being requested (used to track per-domain delays)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            if domain in self.last_request_time:
                elapsed = time.time() - self.last_request_time[domain]
                if elapsed < self.delay:
                    wait_time = self.delay - elapsed
                    self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                    time.sleep(wait_time)
                    
            self.last_request_time[domain] = time.time()
            
        except Exception as e:
            self.logger.error(f"Error in rate limiting: {e}")
            
    def fetch(self, url: str, respect_robots: bool = True) -> Optional[bytes]:
        """
        Fetch URL with politeness rules.
        
        Args:
            url: URL to fetch
            respect_robots: Whether to respect robots.txt (default True)
            
        Returns:
            Response content as bytes, or None if fetch failed
            
        Raises:
            ValueError: If robots.txt disallows fetching
        """
        # Check robots.txt
        if respect_robots and not self.can_fetch(url):
            self.logger.warning(f"Robots.txt disallows fetching: {url}")
            raise ValueError(f"Robots.txt disallows fetching: {url}")
            
        # Respect rate limiting
        self.respect_rate_limit(url)
        
        # Fetch URL
        try:
            self.logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            self.logger.debug(f"Successfully fetched {url} ({len(response.content)} bytes)")
            return response.content
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
            
    def close(self) -> None:
        """Close the session."""
        if self.session:
            self.session.close()
            self.logger.debug("Crawler session closed")
