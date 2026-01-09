"""
YouTube parser using RSS feeds.
Extracts video titles, descriptions, and metadata.
"""

from typing import List, Optional
from datetime import datetime
import requests

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class YouTubeParser(BaseParser):
    """Parser for YouTube content via RSS feeds."""
    
    def __init__(self):
        super().__init__()
        self.feed_url = "https://www.youtube.com/feeds/videos.xml"
        
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse YouTube RSS feed.
        
        Args:
            content: Raw XML content
            url: Source URL
            
        Returns:
            ParserResult object
        """
        try:
            from .rss_parser import RSSParser
            rss_parser = RSSParser()
            
            # Parse as RSS
            result = rss_parser.parse(content, url)
            
            # Override content type
            result.content_type = "youtube"
            result.custom_metadata["platform"] = "youtube"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse YouTube content from {url}: {e}")
            raise ValueError(f"YouTube parsing failed: {e}")
            
    def fetch_channel_videos(
        self,
        channel_id: str,
        max_videos: int = 50
    ) -> List[ParserResult]:
        """
        Fetch videos from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum videos to fetch
            
        Returns:
            List of ParserResult objects
        """
        results = []
        
        try:
            # Build RSS feed URL
            feed_url = f"{self.feed_url}?channel_id={channel_id}"
            
            # Fetch feed
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            
            # Parse entries
            from .rss_parser import RSSParser
            rss_parser = RSSParser()
            entries = rss_parser.parse_entries(response.content, feed_url)
            
            # Convert to YouTube-specific results
            for entry in entries[:max_videos]:
                entry.content_type = "youtube"
                entry.custom_metadata["platform"] = "youtube"
                entry.custom_metadata["channel_id"] = channel_id
                
                # Extract video ID from URL
                if entry.url:
                    video_id = self._extract_video_id(entry.url)
                    if video_id:
                        entry.custom_metadata["video_id"] = video_id
                        
                results.append(entry)
                
            logger.info(f"Fetched {len(results)} videos from channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube channel {channel_id}: {e}")
            
        return results
        
    def fetch_playlist_videos(
        self,
        playlist_id: str,
        max_videos: int = 50
    ) -> List[ParserResult]:
        """
        Fetch videos from a YouTube playlist.
        
        Args:
            playlist_id: YouTube playlist ID
            max_videos: Maximum videos to fetch
            
        Returns:
            List of ParserResult objects
        """
        results = []
        
        try:
            # Build RSS feed URL for playlist
            feed_url = f"{self.feed_url}?playlist_id={playlist_id}"
            
            # Fetch feed
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            
            # Parse entries
            from .rss_parser import RSSParser
            rss_parser = RSSParser()
            entries = rss_parser.parse_entries(response.content, feed_url)
            
            # Convert to YouTube-specific results
            for entry in entries[:max_videos]:
                entry.content_type = "youtube"
                entry.custom_metadata["platform"] = "youtube"
                entry.custom_metadata["playlist_id"] = playlist_id
                
                results.append(entry)
                
            logger.info(f"Fetched {len(results)} videos from playlist {playlist_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube playlist {playlist_id}: {e}")
            
        return results
        
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        import re
        
        patterns = [
            r'watch\?v=([^&]+)',
            r'youtu\.be/([^?]+)',
            r'embed/([^?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
        return None
