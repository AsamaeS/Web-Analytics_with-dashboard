"""
Text cleaning and keyword extraction utilities.
Provides text normalization and intelligent NLP-based keyword extraction.
"""

from typing import List, Dict
import re
from collections import Counter

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextCleaner:
    """Text cleaning and keyword extraction utilities."""
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove HTML artifacts
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\']', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.,!?;:]{2,}', '.', text)
        
        return text.strip()
        
    def get_keyword_frequencies(self, text: str) -> Dict[str, int]:
        """
        Get word frequency distribution.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping words to frequencies
        """
        if not text:
            return {}
            
        # Convert to lowercase
        text = text.lower()
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', text)
        
        # Count frequencies
        return dict(Counter(words))
        
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords using intelligent NLP techniques.
        
        Args:
            text: Input text
            top_n: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        try:
            from .intelligent_keywords import intelligent_extractor
            
            # Use intelligent extraction
            keywords = intelligent_extractor.get_best_keywords(text, top_n=top_n)
            
            # Fallback to basic if empty
            if not keywords:
                keywords = self._extract_keywords_basic(text, top_n)
                
            return keywords
            
        except Exception as e:
            logger.warning(f"Intelligent extraction failed, using fallback: {e}")
            return self._extract_keywords_basic(text, top_n)
            
    def _extract_keywords_basic(self, text: str, top_n: int) -> List[str]:
        """
        Basic keyword extraction (fallback method).
        
        Args:
            text: Input text
            top_n: Number of keywords
            
        Returns:
            List of keywords
        """
        # Get word frequencies
        word_freq = self.get_keyword_frequencies(text)
        
        # Enhanced stopwords
        stopwords = {
            'the', 'is', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'down', 'about', 'which', 'that',
            'this', 'these', 'those', 'it', 'be', 'are', 'was', 'were', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'can', 'may', 'might', 'must', 'should', 'a', 'an', 'as', 'if', 'than',
            'then', 'so', 'such', 'no', 'not', 'only', 'own', 'same', 'just',
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'et', 'ou', 'il', 'elle',
            'wa', 'http', 'https', 'www', 'com'
        }
        
        # Filter and sort
        filtered = [
            (word, freq) for word, freq in word_freq.items()
            if len(word) >= 3 and word.lower() not in stopwords and word.isalpha()
        ]
        
        sorted_keywords = sorted(filtered, key=lambda x: x[1], reverse=True)
        
        return [word for word, _ in sorted_keywords[:top_n]]


# Create global instance
text_cleaner = TextCleaner()


def clean_and_extract_keywords(text: str, top_n: int = 10) -> tuple:
    """
    Clean text and extract keywords.
    
    Args:
        text: Raw text
        top_n: Number of keywords
        
    Returns:
        Tuple of (cleaned_text, keywords)
    """
    cleaned = text_cleaner.clean_text(text)
    keywords = text_cleaner.extract_keywords(cleaned, top_n)
    return cleaned, keywords
