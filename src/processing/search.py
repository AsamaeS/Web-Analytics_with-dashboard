"""
Search functionality using MongoDB full-text search.
Provides keyword-based search with filters and ranking.
"""

from typing import List, Optional
from datetime import datetime

from ..storage import db_manager, SearchQuery, SearchResult, ContentType
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SearchEngine:
    """Search engine for document collection."""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        
    def search(
        self,
        keywords: str,
        source_id: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[SearchResult]:
        """
        Search documents with filters.
        
        Args:
            keywords: Search keywords
            source_id: Optional source filter
            content_type: Optional content type filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            limit: Maximum results
            offset: Results offset for pagination
            
        Returns:
            List of search results
        """
        try:
            # Create search query
            query = SearchQuery(
                keywords=keywords,
                source_id=source_id,
                content_type=content_type,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset
            )
            
            # Execute search
            results = db_manager.search_documents(query)
            
            self.logger.info(f"Search for '{keywords}' returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
            
    def search_with_boolean(
        self,
        keywords: str,
        operator: str = "AND",
        **filters
    ) -> List[SearchResult]:
        """
        Search with boolean operators.
        
        Args:
            keywords: Space-separated keywords
            operator: Boolean operator ("AND" or "OR")
            **filters: Additional search filters
            
        Returns:
            List of search results
        """
        # MongoDB text search supports AND by default
        # For OR, we use quoted phrases or the pipe operator
        
        if operator.upper() == "OR":
            # Convert to OR query: keyword1 | keyword2
            keyword_list = keywords.split()
            keywords = " | ".join(keyword_list)
        elif operator.upper() == "AND":
            # MongoDB default is AND for multiple words
            pass
        else:
            self.logger.warning(f"Unknown boolean operator: {operator}, using AND")
            
        return self.search(keywords=keywords, **filters)
        
    def get_highlighted_snippet(
        self,
        text: str,
        keywords: str,
        max_length: int = 200
    ) -> str:
        """
        Generate snippet with keyword highlighting.
        
        Args:
            text: Full text
            keywords: Search keywords
            max_length: Maximum snippet length
            
        Returns:
            HTML snippet with <mark> tags around keywords
        """
        if not text:
            return ""
            
        # Find keyword positions
        keyword_list = keywords.lower().split()
        text_lower = text.lower()
        
        best_pos = -1
        for keyword in keyword_list:
            pos = text_lower.find(keyword)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
                    
        if best_pos == -1:
            # No keyword found, return beginning
            snippet = text[:max_length]
            if len(text) > max_length:
                snippet += "..."
        else:
            # Extract snippet around keyword
            start = max(0, best_pos - max_length // 2)
            end = min(len(text), best_pos + max_length // 2)
            snippet = text[start:end]
            
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
                
        # Highlight keywords (case-insensitive)
        import re
        for keyword in keyword_list:
            if len(keyword) >= 2:  # Only highlight meaningful keywords
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                snippet = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", snippet)
                
        return snippet


# Global search engine instance
search_engine = SearchEngine()
