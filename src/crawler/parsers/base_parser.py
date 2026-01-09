"""
Base parser interface for content parsers.
Defines the contract that all parsers must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import chardet
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class ParserResult:
    """Standardized parser output."""
    
    def __init__(
        self,
        url: str,
        content_type: str,
        raw_content: str,
        cleaned_text: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        publish_date: Optional[datetime] = None,
        language: Optional[str] = None,
        word_count: int = 0,
        custom_metadata: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        self.content_type = content_type
        self.raw_content = raw_content
        self.cleaned_text = cleaned_text
        self.title = title
        self.author = author
        self.publish_date = publish_date
        self.language = language
        self.word_count = word_count or self._count_words(cleaned_text)
        self.custom_metadata = custom_metadata or {}
        
    @staticmethod
    def _count_words(text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        return len(text.split())
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary matching Document model structure.
        
        Returns:
            Dictionary with url, content_type, raw_content, cleaned_text, and metadata
        """
        return {
            "url": self.url,
            "content_type": self.content_type,
            "raw_content": self.raw_content,
            "cleaned_text": self.cleaned_text,
            "metadata": {
                "title": self.title,
                "author": self.author,
                "publish_date": self.publish_date,
                "language": self.language,
                "word_count": self.word_count,
                "keywords": [],  # To be populated by text processing
                "custom": self.custom_metadata
            }
        }


class BaseParser(ABC):
    """Abstract base class for content parsers."""
    
    def __init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        
    @abstractmethod
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse content and return standardized result.
        
        Args:
            content: Raw content as bytes
            url: Source URL
            
        Returns:
            ParserResult object
            
        Raises:
            ValueError: If content cannot be parsed
        """
        pass
        
    @staticmethod
    def detect_encoding(content: bytes) -> str:
        """
        Detect character encoding of content.
        
        Args:
            content: Raw bytes
            
        Returns:
            Detected encoding string (defaults to 'utf-8')
        """
        try:
            result = chardet.detect(content)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            if confidence > 0.7 and encoding:
                return encoding
            return 'utf-8'
        except Exception:
            return 'utf-8'
            
    @staticmethod
    def decode_content(content: bytes, encoding: Optional[str] = None) -> str:
        """
        Safely decode bytes to string.
        
        Args:
            content: Raw bytes
            encoding: Optional encoding (will auto-detect if not provided)
            
        Returns:
            Decoded string
        """
        if not encoding:
            encoding = BaseParser.detect_encoding(content)
            
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback to utf-8 with error replacement
            try:
                return content.decode('utf-8', errors='replace')
            except Exception:
                # Last resort: latin-1 (never fails)
                return content.decode('latin-1', errors='replace')
                
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Basic text cleaning.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Normalize whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        cleaned = ' '.join(lines)
        
        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
