"""
Plain text parser.
Handles .txt files with various encodings.
"""

from typing import Optional
from datetime import datetime

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class TXTParser(BaseParser):
    """Parser for plain text files."""
    
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse plain text content.
        
        Args:
            content: Raw text content as bytes
            url: Source URL
            
        Returns:
            ParserResult object
            
        Raises:
            ValueError: If content cannot be decoded
        """
        try:
            # Decode content with encoding detection
            text = self.decode_content(content)
            
            if not text:
                raise ValueError("Empty text file")
                
            # Extract basic metadata
            title = self._extract_title(text, url)
            
            # Clean text (minimal processing for plain text)
            cleaned_text = self.clean_text(text)
            
            return ParserResult(
                url=url,
                content_type="txt",
                raw_content=text,
                cleaned_text=cleaned_text,
                title=title,
                custom_metadata={
                    "file_size": len(content),
                    "encoding": self.detect_encoding(content)
                }
            )
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Failed to decode text from {url}: {e}")
            raise ValueError(f"Text decoding failed: {e}")
        except Exception as e:
            self.logger.error(f"Failed to parse text from {url}: {e}")
            raise ValueError(f"Text parsing failed: {e}")
            
    def _extract_title(self, text: str, url: str) -> Optional[str]:
        """
        Extract title from text file.
        Uses first non-empty line or filename from URL.
        
        Args:
            text: Text content
            url: Source URL
            
        Returns:
            Title or None
        """
        # Try to get first line as title
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) < 200:  # Reasonable title length
                return line
                
        # Fallback to filename from URL
        try:
            from urllib.parse import urlparse
            from pathlib import Path
            path = urlparse(url).path
            filename = Path(path).stem  # Get filename without extension
            if filename:
                return filename
        except Exception:
            pass
            
        return None
