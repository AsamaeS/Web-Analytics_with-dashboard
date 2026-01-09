"""
RSS/XML parser using feedparser.
Parses RSS and Atom feeds, treating each entry as a separate document.
"""

from typing import List, Optional
from datetime import datetime
import feedparser
from time import struct_time

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class RSSParser(BaseParser):
    """Parser for RSS and Atom feeds."""
    
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse RSS/Atom feed content.
        
        Note: This returns a single ParserResult for the feed itself.
        Use parse_entries() to get individual entries as separate documents.
        
        Args:
            content: Raw feed content as bytes
            url: Feed URL
            
        Returns:
            ParserResult object for the feed
            
        Raises:
            ValueError: If feed cannot be parsed
        """
        try:
            # Decode content
            feed_text = self.decode_content(content)
            
            # Parse feed
            feed = feedparser.parse(feed_text)
            
            if feed.bozo and not feed.entries:
                # Feed has errors and no entries
                raise ValueError(f"Invalid feed format: {feed.bozo_exception}")
                
            # Extract feed-level metadata
            title = feed.feed.get('title', 'Untitled Feed')
            author = feed.feed.get('author', None)
            language = feed.feed.get('language', None)
            
            # Create summary of feed
            num_entries = len(feed.entries)
            cleaned_text = f"RSS Feed: {title}. Contains {num_entries} entries."
            
            return ParserResult(
                url=url,
                content_type="rss",
                raw_content=feed_text,
                cleaned_text=cleaned_text,
                title=title,
                author=author,
                language=language,
                custom_metadata={
                    "entry_count": num_entries,
                    "feed_type": feed.version
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse RSS feed from {url}: {e}")
            raise ValueError(f"RSS parsing failed: {e}")
            
    def parse_entries(self, content: bytes, feed_url: str) -> List[ParserResult]:
        """
        Parse RSS/Atom feed and return each entry as a separate ParserResult.
        
        Args:
            content: Raw feed content as bytes
            feed_url: Feed URL
            
        Returns:
            List of ParserResult objects, one per feed entry
            
        Raises:
            ValueError: If feed cannot be parsed
        """
        try:
            # Decode content
            feed_text = self.decode_content(content)
            
            # Parse feed
            feed = feedparser.parse(feed_text)
            
            if feed.bozo and not feed.entries:
                raise ValueError(f"Invalid feed format: {feed.bozo_exception}")
                
            results = []
            
            for entry in feed.entries:
                try:
                    result = self._parse_entry(entry, feed_url)
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Failed to parse feed entry: {e}")
                    continue
                    
            self.logger.info(f"Parsed {len(results)} entries from {feed_url}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse RSS feed from {feed_url}: {e}")
            raise ValueError(f"RSS parsing failed: {e}")
            
    def _parse_entry(self, entry: feedparser.FeedParserDict, feed_url: str) -> ParserResult:
        """
        Parse a single feed entry.
        
        Args:
            entry: Feed entry dictionary
            feed_url: Parent feed URL
            
        Returns:
            ParserResult object
        """
        # Extract URL (link)
        url = entry.get('link', feed_url)
        
        # Extract title
        title = entry.get('title', 'Untitled Entry')
        
        # Extract author
        author = entry.get('author', None)
        
        # Extract publication date
        publish_date = self._parse_date(entry.get('published_parsed') or entry.get('updated_parsed'))
        
        # Extract content/summary
        content = ""
        if 'content' in entry and entry.content:
            # Some feeds have multiple content entries
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif 'summary' in entry:
            content = entry.summary
        elif 'description' in entry:
            content = entry.description
            
        # Clean HTML tags from content
        from bs4 import BeautifulSoup
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            cleaned_text = self.clean_text(soup.get_text())
        else:
            cleaned_text = title
            
        # Tags/categories
        tags = []
        if 'tags' in entry:
            tags = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
        return ParserResult(
            url=url,
            content_type="rss",
            raw_content=content or "",
            cleaned_text=cleaned_text,
            title=title,
            author=author,
            publish_date=publish_date,
            custom_metadata={
                "feed_url": feed_url,
                "tags": tags,
                "entry_id": entry.get('id', url)
            }
        )
        
    @staticmethod
    def _parse_date(date_struct: Optional[struct_time]) -> Optional[datetime]:
        """
        Convert feedparser time struct to datetime.
        
        Args:
            date_struct: Time struct from feedparser
            
        Returns:
            datetime object or None
        """
        if not date_struct:
            return None
            
        try:
            from time import mktime
            timestamp = mktime(date_struct)
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError, OverflowError):
            return None
