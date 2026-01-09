"""
PDF parser using PyPDF2.
Extracts text and metadata from PDF documents.
"""

from typing import Optional
from datetime import datetime
import io
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from .base_parser import BaseParser, ParserResult
from ...utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFParser(BaseParser):
    """Parser for PDF documents."""
    
    def parse(self, content: bytes, url: str) -> ParserResult:
        """
        Parse PDF content.
        
        Args:
            content: Raw PDF content as bytes
            url: Source URL
            
        Returns:
            ParserResult object
            
        Raises:
            ValueError: If PDF cannot be parsed
        """
        try:
            # Create PDF reader from bytes
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            
            # Check if encrypted
            if reader.is_encrypted:
                self.logger.warning(f"PDF is encrypted: {url}")
                try:
                    # Try to decrypt with empty password
                    reader.decrypt('')
                except Exception:
                    raise ValueError("PDF is encrypted and cannot be decrypted")
                    
            # Extract metadata
            metadata = reader.metadata
            title = self._extract_title(metadata)
            author = self._extract_author(metadata)
            creation_date = self._extract_creation_date(metadata)
            
            # Extract text from all pages
            text_parts = []
            num_pages = len(reader.pages)
            
            for page_num in range(num_pages):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
                    
            if not text_parts:
                self.logger.warning(f"No text extracted from PDF: {url}")
                raw_text = ""
                cleaned_text = ""
            else:
                raw_text = "\n\n".join(text_parts)
                cleaned_text = self.clean_text(raw_text)
                
            return ParserResult(
                url=url,
                content_type="pdf",
                raw_content=raw_text,
                cleaned_text=cleaned_text,
                title=title,
                author=author,
                publish_date=creation_date,
                custom_metadata={
                    "num_pages": num_pages,
                    "is_encrypted": reader.is_encrypted
                }
            )
            
        except PdfReadError as e:
            self.logger.error(f"Failed to read PDF from {url}: {e}")
            raise ValueError(f"Invalid or corrupted PDF: {e}")
        except Exception as e:
            self.logger.error(f"Failed to parse PDF from {url}: {e}")
            raise ValueError(f"PDF parsing failed: {e}")
            
    def _extract_title(self, metadata) -> Optional[str]:
        """Extract title from PDF metadata."""
        if not metadata:
            return None
            
        try:
            title = metadata.get('/Title', None)
            if title:
                return str(title).strip()
        except Exception:
            pass
            
        return None
        
    def _extract_author(self, metadata) -> Optional[str]:
        """Extract author from PDF metadata."""
        if not metadata:
            return None
            
        try:
            author = metadata.get('/Author', None)
            if author:
                return str(author).strip()
        except Exception:
            pass
            
        return None
        
    def _extract_creation_date(self, metadata) -> Optional[datetime]:
        """
        Extract creation date from PDF metadata.
        
        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
        Example: D:20230101120000+01'00'
        """
        if not metadata:
            return None
            
        try:
            date_str = metadata.get('/CreationDate', None)
            if not date_str:
                date_str = metadata.get('/ModDate', None)
                
            if date_str:
                # Remove D: prefix
                date_str = str(date_str)
                if date_str.startswith('D:'):
                    date_str = date_str[2:]
                    
                # Extract date components (YYYYMMDDHHMMSS)
                if len(date_str) >= 14:
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    hour = int(date_str[8:10])
                    minute = int(date_str[10:12])
                    second = int(date_str[12:14])
                    
                    return datetime(year, month, day, hour, minute, second)
        except (ValueError, IndexError, AttributeError) as e:
            self.logger.debug(f"Failed to parse PDF date: {e}")
            pass
            
        return None
