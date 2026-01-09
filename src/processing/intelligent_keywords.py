"""
Intelligent keyword extraction using NLP techniques.
Implements stopwords removal, lemmatization, TF-IDF, RAKE, and n-grams.
"""

from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import re
import math

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import NLTK, but gracefully handle if not available
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    from nltk.util import ngrams as nltk_ngrams
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, using fallback keyword extraction")

# Try to import sklearn for TF-IDF
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, TF-IDF disabled")

# Try to import RAKE
try:
    from rake_nltk import Rake
    RAKE_AVAILABLE = True
except ImportError:
    RAKE_AVAILABLE = False
    logger.warning("RAKE not available, RAKE extraction disabled")


class IntelligentKeywordExtractor:
    """
    Advanced keyword extraction using multiple NLP techniques.
    Combines stopwords filtering, lemmatization, TF-IDF, RAKE, and n-grams.
    """
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize extractor.
        
        Args:
            languages: List of languages for stopwords (default: ['english', 'french'])
        """
        self.languages = languages or ['english', 'french']
        self.stopwords = self._load_stopwords()
        self.lemmatizer = None
        
        if NLTK_AVAILABLE:
            try:
                self.lemmatizer = WordNetLemmatizer()
                # Download required NLTK data
                self._download_nltk_data()
            except Exception as e:
                logger.warning(f"Failed to initialize lemmatizer: {e}")
                
    def _download_nltk_data(self):
        """Download required NLTK data silently."""
        required_data = [
            ('corpora', 'stopwords'),
            ('corpora', 'wordnet'),
            ('tokenizers', 'punkt'),
            ('tokenizers', 'punkt_tab'),
            ('taggers', 'averaged_perceptron_tagger'),
            ('taggers', 'averaged_perceptron_tagger_eng'),
        ]
        
        for data_type, data_name in required_data:
            try:
                # Try to find the data
                if data_type == 'corpora':
                    nltk.data.find(f'{data_type}/{data_name}')
                elif data_type == 'tokenizers':
                    nltk.data.find(f'{data_type}/{data_name}')
                elif data_type == 'taggers':
                    nltk.data.find(f'{data_type}/{data_name}')
            except LookupError:
                try:
                    logger.info(f"Downloading NLTK data: {data_name}")
                    nltk.download(data_name, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download {data_name}: {e}")
                    
    def _load_stopwords(self) -> Set[str]:
        """Load stopwords for multiple languages."""
        all_stopwords = set()
        
        if NLTK_AVAILABLE:
            for lang in self.languages:
                try:
                    lang_stops = set(stopwords.words(lang))
                    all_stopwords.update(lang_stops)
                except Exception as e:
                    logger.warning(f"Failed to load stopwords for {lang}: {e}")
                    
        # Add custom stopwords
        custom_stops = {
            # English
            'the', 'is', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'down', 'about', 'over', 'under',
            'which', 'that', 'this', 'these', 'those', 'them', 'they', 'their',
            'there', 'where', 'when', 'why', 'how', 'what', 'who', 'whom',
            'it', 'its', 'be', 'been', 'being', 'am', 'are', 'was', 'were',
            'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must',
            'have', 'has', 'had', 'do', 'does', 'did', 'done', 'doing',
            'a', 'an', 'as', 'if', 'than', 'then', 'so', 'such', 'out', 'into',
            # French
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'au', 'aux',
            'ce', 'se', 'ces', 'ses', 'son', 'sa', 'leur', 'leurs', 'mon', 'ma',
            'ton', 'ta', 'mes', 'tes', 'notre', 'votre', 'nos', 'vos',
            'il', 'elle', 'ils', 'elles', 'on', 'nous', 'vous', 'je', 'tu',
            'et', 'ou', 'mais', 'donc', 'car', 'ni', 'que', 'qui', 'quoi',
            'dont', 'où', 'comment', 'pourquoi', 'quand', 'combien',
            'dans', 'sur', 'sous', 'avec', 'sans', 'pour', 'par', 'en',
            'être', 'avoir', 'faire', 'dire', 'aller', 'voir', 'savoir',
            'pouvoir', 'vouloir', 'devoir', 'falloir', 'mettre', 'prendre',
            # Common noise
            'wa', 'http', 'https', 'www', 'com', 'org', 'net', 'html',
        }
        all_stopwords.update(custom_stops)
        
        return all_stopwords
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text.lower())
            except Exception:
                pass
                
        # Fallback tokenization
        return re.findall(r'\b\w+\b', text.lower())
        
    def _lemmatize(self, word: str) -> str:
        """Lemmatize a word."""
        if self.lemmatizer:
            try:
                return self.lemmatizer.lemmatize(word)
            except Exception:
                pass
        return word
        
    def _is_valid_word(self, word: str, min_length: int = 3) -> bool:
        """Check if word is valid for keyword extraction."""
        if len(word) < min_length:
            return False
        if word in self.stopwords:
            return False
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', word):
            return False
        if word.isdigit():
            return False
        return True
        
    def extract_keywords_basic(
        self,
        text: str,
        top_n: int = 20,
        min_freq: int = 2
    ) -> List[Tuple[str, int]]:
        """
        Basic keyword extraction with stopwords and lemmatization.
        
        Args:
            text: Input text
            top_n: Number of top keywords
            min_freq: Minimum frequency
            
        Returns:
            List of (keyword, frequency) tuples
        """
        # Tokenize
        tokens = self._tokenize(text)
        
        # Filter and lemmatize
        filtered_tokens = []
        for token in tokens:
            if self._is_valid_word(token):
                lemma = self._lemmatize(token)
                if self._is_valid_word(lemma):
                    filtered_tokens.append(lemma)
                    
        # Count frequencies
        freq = Counter(filtered_tokens)
        
        # Filter by minimum frequency
        keywords = [(word, count) for word, count in freq.most_common() if count >= min_freq]
        
        return keywords[:top_n]
        
    def extract_keywords_tfidf(
        self,
        documents: List[str],
        top_n: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF.
        
        Args:
            documents: List of document texts
            top_n: Number of top keywords
            
        Returns:
            List of (keyword, score) tuples
        """
        if not SKLEARN_AVAILABLE or not documents:
            logger.warning("TF-IDF extraction not available")
            return []
            
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=top_n * 2,
                min_df=2,
                max_df=0.8,
                stop_words=list(self.stopwords),
                ngram_range=(1, 2),
                token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b'
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            avg_scores = tfidf_matrix.mean(axis=0).A1
            
            # Sort by score
            top_indices = avg_scores.argsort()[-top_n:][::-1]
            keywords = [(feature_names[i], avg_scores[i]) for i in top_indices]
            
            return keywords
            
        except Exception as e:
            logger.error(f"TF-IDF extraction failed: {e}")
            return []
            
    def extract_keywords_rake(
        self,
        text: str,
        top_n: int = 20
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords using RAKE algorithm.
        
        Args:
            text: Input text
            top_n: Number of top keywords
            
        Returns:
            List of (keyword, score) tuples
        """
        if not RAKE_AVAILABLE:
            logger.warning("RAKE extraction not available")
            return []
            
        try:
            rake = Rake(
                stopwords=list(self.stopwords),
                min_length=1,
                max_length=3
            )
            
            rake.extract_keywords_from_text(text)
            keywords = rake.get_ranked_phrases_with_scores()[:top_n]
            
            # Reverse order (RAKE returns (score, phrase))
            return [(phrase, score) for score, phrase in keywords]
            
        except Exception as e:
            logger.error(f"RAKE extraction failed: {e}")
            return []
            
    def extract_ngrams(
        self,
        text: str,
        n: int = 2,
        top_n: int = 20,
        min_freq: int = 2
    ) -> List[Tuple[str, int]]:
        """
        Extract n-grams from text.
        
        Args:
            text: Input text
            n: N-gram size (2=bigrams, 3=trigrams)
            top_n: Number of top n-grams
            min_freq: Minimum frequency
            
        Returns:
            List of (ngram, frequency) tuples
        """
        # Tokenize
        tokens = self._tokenize(text)
        
        # Filter tokens
        filtered_tokens = [
            self._lemmatize(token)
            for token in tokens
            if self._is_valid_word(token)
        ]
        
        if len(filtered_tokens) < n:
            return []
            
        # Generate n-grams
        if NLTK_AVAILABLE:
            ngram_list = list(nltk_ngrams(filtered_tokens, n))
        else:
            # Fallback n-gram generation
            ngram_list = [
                tuple(filtered_tokens[i:i+n])
                for i in range(len(filtered_tokens) - n + 1)
            ]
            
        # Join n-grams into strings
        ngram_strings = [' '.join(ng) for ng in ngram_list]
        
        # Count frequencies
        freq = Counter(ngram_strings)
        
        # Filter and return
        keywords = [(ng, count) for ng, count in freq.most_common() if count >= min_freq]
        
        return keywords[:top_n]
        
    def extract_all(
        self,
        text: str,
        documents: List[str] = None,
        top_n: int = 20
    ) -> Dict[str, List[Tuple]]:
        """
        Extract keywords using all available methods.
        
        Args:
            text: Input text
            documents: Additional documents for TF-IDF
            top_n: Number of top keywords per method
            
        Returns:
            Dictionary with results from each method
        """
        results = {}
        
        # Basic extraction
        results['basic'] = self.extract_keywords_basic(text, top_n)
        
        # TF-IDF (if documents provided)
        if documents:
            results['tfidf'] = self.extract_keywords_tfidf(documents, top_n)
            
        # RAKE
        results['rake'] = self.extract_keywords_rake(text, top_n)
        
        # Bigrams
        results['bigrams'] = self.extract_ngrams(text, n=2, top_n=top_n)
        
        # Trigrams
        results['trigrams'] = self.extract_ngrams(text, n=3, top_n=top_n)
        
        return results
        
    def get_best_keywords(
        self,
        text: str,
        documents: List[str] = None,
        top_n: int = 20
    ) -> List[str]:
        """
        Get best keywords combining multiple methods.
        
        Args:
            text: Input text
            documents: Additional documents for TF-IDF
            top_n: Number of final keywords
            
        Returns:
            List of best keywords
        """
        all_results = self.extract_all(text, documents, top_n=top_n*2)
        
        # Combine and weight results
        keyword_scores = {}
        
        # Basic: weight 1.0
        for word, freq in all_results.get('basic', []):
            keyword_scores[word] = keyword_scores.get(word, 0) + freq * 1.0
            
        # TF-IDF: weight 2.0
        for word, score in all_results.get('tfidf', []):
            keyword_scores[word] = keyword_scores.get(word, 0) + score * 100 * 2.0
            
        # RAKE: weight 1.5
        for phrase, score in all_results.get('rake', []):
            keyword_scores[phrase] = keyword_scores.get(phrase, 0) + score * 1.5
            
        # Bigrams: weight 1.2
        for ng, freq in all_results.get('bigrams', []):
            keyword_scores[ng] = keyword_scores.get(ng, 0) + freq * 1.2
            
        # Sort by combined score
        sorted_keywords = sorted(
            keyword_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [kw for kw, _ in sorted_keywords[:top_n]]


# Create global instance
intelligent_extractor = IntelligentKeywordExtractor()
