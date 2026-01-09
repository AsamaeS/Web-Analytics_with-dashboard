"""
Tests for parser modules.
"""

import pytest
from src.crawler.parsers import HTMLParser, RSSParser, PDFParser, TXTParser


class TestHTMLParser:
    """Tests for HTML parser."""
    
    def test_parse_simple_html(self):
        """Test parsing simple HTML."""
        parser = HTMLParser()
        html = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Welcome</h1>
                <p>This is a test page.</p>
            </body>
        </html>
        """
        
        result = parser.parse(html, "http://example.com/test")
        
        assert result.title == "Test Page"
        assert "Welcome" in result.cleaned_text
        assert "test page" in result.cleaned_text
        assert result.content_type == "html"
        
    def test_parse_with_metadata(self):
        """Test parsing HTML with metadata."""
        parser = HTMLParser()
        html = b"""
        <html>
            <head>
                <title>Article</title>
                <meta name="author" content="John Doe">
                <meta property="article:published_time" content="2023-01-01T00:00:00Z">
            </head>
            <body><p>Content here</p></body>
        </html>
        """
        
        result = parser.parse(html, "http://example.com/article")
        
        assert result.title == "Article"
        assert result.author == "John Doe"
        assert result.publish_date is not None


class TestRSSParser:
    """Tests for RSS parser."""
    
    def test_parse_rss_feed(self):
        """Test parsing RSS feed."""
        parser = RSSParser()
        rss = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article 1</title>
                    <description>Description 1</description>
                    <link>http://example.com/1</link>
                </item>
                <item>
                    <title>Article 2</title>
                    <description>Description 2</description>
                    <link>http://example.com/2</link>
                </item>
            </channel>
        </rss>
        """
        
        results = parser.parse_entries(rss, "http://example.com/feed")
        
        assert len(results) == 2
        assert results[0].title == "Article 1"
        assert results[1].title == "Article 2"
        assert all(r.content_type == "rss" for r in results)


class TestPDFParser:
    """Tests for PDF parser."""
    
    def test_parse_pdf_error_handling(self):
        """Test PDF parser error handling."""
        parser = PDFParser()
        invalid_pdf = b"This is not a PDF"
        
        with pytest.raises(ValueError):
            parser.parse(invalid_pdf, "http://example.com/test.pdf")


class TestTXTParser:
    """Tests for TXT parser."""
    
    def test_parse_text(self):
        """Test parsing plain text."""
        parser = TXTParser()
        text = b"This is a simple text file.\nIt has multiple lines.\n"
        
        result = parser.parse(text, "http://example.com/test.txt")
        
        assert "simple text file" in result.cleaned_text
        assert result.content_type == "txt"
        assert result.title is not None
