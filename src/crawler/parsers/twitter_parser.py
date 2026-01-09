"""
Twitter/X parser using RSS feeds and basic scraping.
Extracts tweets from user timelines and search results.
"""

from typing import List, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class TwitterParser(BaseParser):
    """Parser for Twitter/X content via Nitter RSS or scraping."""
    
    def __init__(self):
        super().__init__()
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.poast.org",
            "https://nitter.privacydev.net"
        ]
        
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse Twitter content.
        
        Args:
            content: Raw content
            url: Source URL
            
        Returns:
            ParserResult object
        """
        try:
            text = self.decode_content(content)
            soup = BeautifulSoup(text, 'html.parser')
            
            # Extract tweets
            tweets = self._extract_tweets(soup)
            
            # Combine all tweet text
            all_text = "\n\n".join([t['text'] for t in tweets])
            cleaned_text = self.clean_text(all_text)
            
            # Get username from URL
            username = self._extract_username(url)
            
            return ParserResult(
                url=url,
                content_type="twitter",
                raw_content=text,
                cleaned_text=cleaned_text,
                title=f"Twitter: @{username}" if username else "Twitter Feed",
                custom_metadata={
                    "tweet_count": len(tweets),
                    "platform": "twitter"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Twitter content from {url}: {e}")
            raise ValueError(f"Twitter parsing failed: {e}")
            
    def fetch_user_timeline(self, username: str, max_tweets: int = 100) -> List[ParserResult]:
        """
        Fetch user timeline via Nitter RSS.
        
        Args:
            username: Twitter username
            max_tweets: Maximum tweets to fetch
            
        Returns:
            List of ParserResult objects
        """
        results = []
        
        for instance in self.nitter_instances:
            try:
                # Try Nitter RSS feed
                rss_url = f"{instance}/{username}/rss"
                response = requests.get(rss_url, timeout=10)
                
                if response.status_code == 200:
                    # Parse RSS
                    from .rss_parser import RSSParser
                    rss_parser = RSSParser()
                    entries = rss_parser.parse_entries(response.content, rss_url)
                    
                    # Convert to Twitter-specific results
                    for entry in entries[:max_tweets]:
                        entry.content_type = "twitter"
                        entry.custom_metadata["platform"] = "twitter"
                        entry.custom_metadata["username"] = username
                        results.append(entry)
                    
                    logger.info(f"Fetched {len(results)} tweets from @{username}")
                    return results
                    
            except Exception as e:
                logger.warning(f"Failed to fetch from {instance}: {e}")
                continue
                
        if not results:
            logger.error(f"Failed to fetch tweets for @{username} from all instances")
            
        return results
        
    def _extract_tweets(self, soup: BeautifulSoup) -> List[dict]:
        """Extract tweets from HTML."""
        tweets = []
        
        # Try multiple selectors for tweet containers
        tweet_selectors = [
            '.tweet-content',
            '.timeline-item',
            'article[data-tweet-id]'
        ]
        
        for selector in tweet_selectors:
            elements = soup.select(selector)
            if elements:
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text:
                        tweets.append({'text': text})
                break
                
        return tweets
        
    def _extract_username(self, url: str) -> Optional[str]:
        """Extract username from Twitter URL."""
        match = re.search(r'twitter\.com/([^/]+)', url, re.IGNORECASE)
        if not match:
            match = re.search(r'nitter\.[^/]+/([^/]+)', url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
