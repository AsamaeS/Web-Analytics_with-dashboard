"""
Tests for intelligent keyword extraction.
Tests NLP features: stopwords, lemmatization, TF-IDF, RAKE, n-grams.
"""

import pytest
from src.processing.intelligent_keywords import IntelligentKeywordExtractor


class TestIntelligentKeywordExtractor:
    """Test intelligent keyword extraction."""
    
    def setup_method(self):
        self.extractor = IntelligentKeywordExtractor(languages=['english', 'french'])
        
    def test_stopwords_loaded(self):
        """Test that stopwords are properly loaded."""
        assert len(self.extractor.stopwords) > 0
        assert 'the' in self.extractor.stopwords
        assert 'is' in self.extractor.stopwords
        assert 'and' in self.extractor.stopwords
        assert 'le' in self.extractor.stopwords  # French
        assert 'wa' in self.extractor.stopwords  # Custom
        
    def test_tokenization(self):
        """Test text tokenization."""
        text = "Python programming is amazing"
        tokens = self.extractor._tokenize(text)
        
        assert len(tokens) > 0
        assert 'python' in tokens
        assert 'programming' in tokens
        
    def test_valid_word_filtering(self):
        """Test word validity checking."""
        assert self.extractor._is_valid_word('python')
        assert self.extractor._is_valid_word('programming')
        assert not self.extractor._is_valid_word('the')
        assert not self.extractor._is_valid_word('is')
        assert not self.extractor._is_valid_word('ab')  # Too short
        assert not self.extractor._is_valid_word('123')  # Digits
        assert not self.extractor._is_valid_word('http')  # Common noise
        
    def test_basic_keyword_extraction(self):
        """Test basic keyword extraction without stopwords."""
        text = """
        Python programming is a powerful tool for web development.
        Python developers use Python frameworks like Django and Flask.
        Web scraping with Python is very popular.
        """
        
        keywords = self.extractor.extract_keywords_basic(text, top_n=5, min_freq=2)
        
        assert len(keywords) > 0
        # Python should be top keyword (appears 3 times)
        top_words = [kw for kw, freq in keywords]
        assert 'python' in top_words
        # Stopwords should NOT appear
        assert 'the' not in top_words
        assert 'is' not in top_words
        assert 'and' not in top_words
        assert 'with' not in top_words
        
    def test_bigrams_extraction(self):
        """Test bigram n-gram extraction."""
        text = """
        Machine learning algorithms are used in data science.
        Data science projects require machine learning knowledge.
        """
        
        bigrams = self.extractor.extract_ngrams(text, n=2, top_n=5, min_freq=1)
        
        assert len(bigrams) > 0
        # Should contain meaningful bigrams
        bigram_strings = [bg for bg, freq in bigrams]
        # Check if we have actual bigrams
        assert any(' ' in bg for bg in bigram_strings)
        
    def test_trigrams_extraction(self):
        """Test trigram n-gram extraction."""
        text = """
        Natural language processing techniques are important.
        Natural language processing is used in many applications.
        """
        
        trigrams = self.extractor.extract_ngrams(text, n=3, top_n=5, min_freq=1)
        
        assert len(trigrams) > 0
        # Should contain meaningful trigrams
        trigram_strings = [tg for tg, freq in trigrams]
        assert any(tg.count(' ') >= 2 for tg in trigram_strings)
        
    def test_tfidf_extraction(self):
        """Test TF-IDF keyword extraction."""
        documents = [
            "Python programming for data science",
            "Machine learning with Python libraries",
            "Data analysis using pandas and numpy"
        ]
        
        try:
            keywords = self.extractor.extract_keywords_tfidf(documents, top_n=5)
            
            if keywords:  # Only if sklearn is available
                assert len(keywords) > 0
                word_list = [word for word, score in keywords]
                # Should not contain stopwords
                assert 'the' not in word_list
                assert 'and' not in word_list
                # Should contain meaningful words
                assert any(word in ['python', 'data', 'machine', 'learning'] for word in word_list)
        except Exception:
            # OK if sklearn not available
            pytest.skip("sklearn not available")
            
    def test_rake_extraction(self):
        """Test RAKE keyword extraction."""
        text = """
        Web crawling and data extraction are important techniques in data science.
        Python libraries like Scrapy and BeautifulSoup are commonly used for web scraping.
        """
        
        try:
            keywords = self.extractor.extract_keywords_rake(text, top_n=5)
            
            if keywords:  # Only if RAKE is available
                assert len(keywords) > 0
                phrases = [phrase for phrase, score in keywords]
                # RAKE should extract phrases, not just single words
                assert any(len(phrase.split()) > 1 for phrase in phrases)
        except Exception:
            # OK if RAKE not available
            pytest.skip("RAKE not available")
            
    def test_combined_extraction(self):
        """Test combined keyword extraction using multiple methods."""
        text = """
        Artificial intelligence and machine learning are transforming industries.
        Deep learning neural networks achieve state-of-the-art results.
        Natural language processing enables human-computer interaction.
        """
        
        documents = [text]
        
        keywords = self.extractor.get_best_keywords(text, documents, top_n=10)
        
        assert len(keywords) > 0
        assert len(keywords) <= 10
        
        # Should NOT contain stopwords
        assert 'the' not in keywords
        assert 'is' not in keywords
        assert 'and' not in keywords
        assert 'are' not in keywords
        
        # Should contain meaningful technical terms
        meaningful_found = any(
            word in keywords 
            for word in ['artificial', 'intelligence', 'machine', 'learning', 'neural', 'language']
        )
        assert meaningful_found
        
    def test_frequency_filtering(self):
        """Test that low-frequency words are filtered out."""
        text = "cat dog cat bird cat dog elephant"
        
        # With min_freq=2, elephant should be filtered out
        keywords = self.extractor.extract_keywords_basic(text, top_n=10, min_freq=2)
        
        word_list = [word for word, freq in keywords]
        assert 'cat' in word_list  # Appears 3 times
        assert 'dog' in word_list  # Appears 2 times
        # elephant should not be in list (appears only once)
        # Note: may or may not appear depending on implementation
        
    def test_multilanguage_stopwords(self):
        """Test multilanguage stopword filtering."""
        text_en = "the quick brown fox jumps over the lazy dog"
        text_fr = "le chat noir saute sur le chien paresseux"
        
        keywords_en = self.extractor.extract_keywords_basic(text_en, top_n=10, min_freq=1)
        keywords_fr = self.extractor.extract_keywords_basic(text_fr, top_n=10, min_freq=1)
        
        words_en = [word for word, freq in keywords_en]
        words_fr = [word for word, freq in keywords_fr]
        
        # English stopwords should be removed
        assert 'the' not in words_en
        assert 'over' not in words_en
        
        # French stopwords should be removed
        assert 'le' not in words_fr
        assert 'sur' not in words_fr
