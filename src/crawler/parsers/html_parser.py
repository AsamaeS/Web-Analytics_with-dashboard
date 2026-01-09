"""
HTML parser using BeautifulSoup4.
Extracts visible text content, title, and metadata from HTML pages.
"""

from typing import Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag
import re

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger
from ...utils.config import settings

logger = setup_logger(__name__)


class HTMLParser(BaseParser):
    """Parser for HTML content."""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.crawler_user_agent
        })
        
    def fetch_and_parse(self, url: str) -> ParserResult:
        """
        Fetch URL and parse HTML content.
        
        Args:
            url: URL to fetch
            
        Returns:
            ParserResult object
            
        Raises:
            ValueError: If request fails or content cannot be parsed
        """
        try:
            response = self.session.get(
                url,
                timeout=settings.request_timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            return self.parse(response.content, url)
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            raise ValueError(f"Failed to fetch URL: {e}")
            
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse HTML content.
        
        Args:
            content: Raw HTML content as bytes
            url: Source URL
            
        Returns:
            ParserResult object
            
        Raises:
            ValueError: If HTML cannot be parsed
        """
        try:
            # Decode content
            html_text = self.decode_content(content)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_text, 'lxml')
            
            # Extract metadata
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            language = self._extract_language(soup)
            
            # Extract and clean text content
            visible_text = self._extract_visible_text(soup)
            cleaned_text = self.clean_text(visible_text)
            
            # Detect pagination
            next_page = self._detect_next_page(soup, url)
            custom_metadata = {"next_page": next_page} if next_page else {}
            
            return ParserResult(
                url=url,
                content_type="html",
                raw_content=html_text,
                cleaned_text=cleaned_text,
                title=title,
                author=author,
                publish_date=publish_date,
                language=language,
                custom_metadata=custom_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse HTML from {url}: {e}")
            raise ValueError(f"HTML parsing failed: {e}")
            
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        # Try <title> tag first
        if soup.title and soup.title.string:
            return soup.title.string.strip()
            
        # Try meta og:title
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
            
        # Try h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
            
        return None
        
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from metadata."""
        # Try meta author tag
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
            
        # Try meta article:author
        meta_author = soup.find('meta', property='article:author')
        if meta_author and meta_author.get('content'):
            return meta_author['content'].strip()
            
        return None
        
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publication date from metadata."""
        # Try meta article:published_time
        meta_date = soup.find('meta', property='article:published_time')
        if not meta_date:
            meta_date = soup.find('meta', attrs={'name': 'publication_date'})
        if not meta_date:
            meta_date = soup.find('meta', attrs={'name': 'date'})
            
        if meta_date and meta_date.get('content'):
            date_str = meta_date['content']
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
                
        return None
        
    def _extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract language from HTML lang attribute."""
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang'].strip()
        return None
        
    def _extract_visible_text(self, soup: BeautifulSoup) -> str:
        """
        Extract visible text content, excluding scripts, styles, and navigation.
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            element.decompose()
            
        # Get text from main content areas (prefer article, main, or body)
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
            
        return text
        
    def _detect_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Detect pagination link (next page).
        
        Args:
            soup: BeautifulSoup object
            current_url: Current page URL
            
        Returns:
            Next page URL or None
        """
        # Common pagination patterns
        next_patterns = [
            {'rel': 'next'},
            {'class': re.compile(r'next', re.I)},
            {'id': re.compile(r'next', re.I)}
        ]
        
        for pattern in next_patterns:
            next_link = soup.find('a', pattern)
            if next_link and next_link.get('href'):
                href = next_link['href']
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    return urljoin(current_url, href)
                elif href.startswith('http'):
                    return href
                    
        return None
