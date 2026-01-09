"""
Reddit parser for subreddits, posts, and comments.
Uses Reddit JSON API (no authentication required for public content).
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
import time

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class RedditParser(BaseParser):
    """Parser for Reddit content via JSON API."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.reddit.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse Reddit content.
        
        Args:
            content: Raw JSON content
            url: Source URL
            
        Returns:
            ParserResult object
        """
        try:
            import json
            data = json.loads(content)
            
            # Extract posts from JSON
            posts = self._extract_posts(data)
            
            # Combine all post text
            all_text = "\n\n".join([
                f"{p.get('title', '')}\n{p.get('selftext', '')}"
                for p in posts
            ])
            
            cleaned_text = self.clean_text(all_text)
            
            subreddit = self._extract_subreddit(url)
            
            return ParserResult(
                url=url,
                content_type="reddit",
                raw_content=content.decode('utf-8'),
                cleaned_text=cleaned_text,
                title=f"r/{subreddit}" if subreddit else "Reddit Feed",
                custom_metadata={
                    "post_count": len(posts),
                    "platform": "reddit",
                    "subreddit": subreddit
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Reddit content from {url}: {e}")
            raise ValueError(f"Reddit parsing failed: {e}")
            
    def fetch_subreddit(
        self,
        subreddit: str,
        sort: str = "hot",
        limit: int = 100
    ) -> List[ParserResult]:
        """
        Fetch posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            sort: Sort type (hot, new, top, rising)
            limit: Maximum posts to fetch
            
        Returns:
            List of ParserResult objects
        """
        results = []
        
        try:
            # Fetch subreddit JSON
            url = f"{self.base_url}/r/{subreddit}/{sort}.json"
            params = {'limit': min(limit, 100)}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', {}).get('children', [])
            
            for post_data in posts[:limit]:
                post = post_data.get('data', {})
                
                # Create result for each post
                title = post.get('title', '')
                selftext = post.get('selftext', '')
                author = post.get('author', '')
                created = post.get('created_utc', 0)
                
                text = f"{title}\n\n{selftext}"
                cleaned = self.clean_text(text)
                
                result = ParserResult(
                    url=post.get('url', ''),
                    content_type="reddit",
                    raw_content=text,
                    cleaned_text=cleaned,
                    title=title,
                    author=author,
                    publish_date=datetime.fromtimestamp(created) if created else None,
                    custom_metadata={
                        "platform": "reddit",
                        "subreddit": subreddit,
                        "score": post.get('score', 0),
                        "num_comments": post.get('num_comments', 0),
                        "post_id": post.get('id', '')
                    }
                )
                
                results.append(result)
                
            logger.info(f"Fetched {len(results)} posts from r/{subreddit}")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to fetch r/{subreddit}: {e}")
            
        return results
        
    def fetch_post_comments(
        self,
        subreddit: str,
        post_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments from a specific post.
        
        Args:
            subreddit: Subreddit name
            post_id: Post ID
            limit: Maximum comments to fetch
            
        Returns:
            List of comment dictionaries
        """
        comments = []
        
        try:
            url = f"{self.base_url}/r/{subreddit}/comments/{post_id}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Comments are in the second element
            if len(data) > 1:
                comment_data = data[1].get('data', {}).get('children', [])
                
                for comment in comment_data[:limit]:
                    c = comment.get('data', {})
                    if c.get('body'):
                        comments.append({
                            'author': c.get('author', ''),
                            'body': c.get('body', ''),
                            'score': c.get('score', 0),
                            'created': c.get('created_utc', 0)
                        })
                        
            logger.info(f"Fetched {len(comments)} comments from post {post_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch comments: {e}")
            
        return comments
        
    def _extract_posts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract posts from Reddit JSON."""
        if isinstance(data, dict):
            children = data.get('data', {}).get('children', [])
            return [child.get('data', {}) for child in children]
        return []
        
    def _extract_subreddit(self, url: str) -> Optional[str]:
        """Extract subreddit name from URL."""
        import re
        match = re.search(r'/r/([^/]+)', url)
        if match:
            return match.group(1)
        return None
