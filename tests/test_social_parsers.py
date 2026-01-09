"""
Comprehensive tests for social media parsers.
Tests Twitter, Reddit, YouTube, and LinkedIn parsers.
"""

import pytest
from src.crawler.parsers import TwitterParser, RedditParser, YouTubeParser, LinkedInParser, ParserResult


class TestTwitterParser:
    """Test Twitter/X parser."""
    
    def setup_method(self):
        self.parser = TwitterParser()
        
    def test_extract_username_from_url(self):
        """Test username extraction from various URL formats."""
        url1 = "https://twitter.com/elonmusk"
        url2 = "https://nitter.net/elonmusk"
        
        username1 = self.parser._extract_username(url1)
        username2 = self.parser._extract_username(url2)
        
        assert username1 == "elonmusk"
        assert username2 == "elonmusk"
        
    def test_parse_basic_content(self):
        """Test parsing basic Twitter content."""
        html_content = b"""
        <div class="tweet-content">
            <p>This is a test tweet about Python programming and web crawling.</p>
        </div>
        """
        
        result = self.parser.parse(html_content, "https://twitter.com/test")
        
        assert isinstance(result, ParserResult)
        assert result.content_type == "twitter"
        assert "Python" in result.cleaned_text or "python" in result.cleaned_text
        assert result.custom_metadata["platform"] == "twitter"


class TestRedditParser:
    """Test Reddit parser."""
    
    def setup_method(self):
        self.parser = RedditParser()
        
    def test_extract_subreddit_from_url(self):
        """Test subreddit extraction from URL."""
        url = "https://reddit.com/r/python"
        subreddit = self.parser._extract_subreddit(url)
        
        assert subreddit == "python"
        
    def test_parse_reddit_json(self):
        """Test parsing Reddit JSON data."""
        json_content = b"""{
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Test Post",
                            "selftext": "This is a test post about Python",
                            "score": 100,
                            "num_comments": 50
                        }
                    }
                ]
            }
        }"""
        
        result = self.parser.parse(json_content, "https://reddit.com/r/python")
        
        assert isinstance(result, ParserResult)
        assert result.content_type == "reddit"
        assert "Test Post" in result.cleaned_text
        assert result.custom_metadata["platform"] == "reddit"
        
    def test_extract_posts_from_json(self):
        """Test post extraction from JSON."""
        data = {
            "data": {
                "children": [
                    {"data": {"title": "Post 1"}},
                    {"data": {"title": "Post 2"}}
                ]
            }
        }
        
        posts = self.parser._extract_posts(data)
        
        assert len(posts) == 2
        assert posts[0]["title"] == "Post 1"
        assert posts[1]["title"] == "Post 2"


class TestYouTubeParser:
    """Test YouTube parser."""
    
    def setup_method(self):
        self.parser = YouTubeParser()
        
    def test_extract_video_id_from_url(self):
        """Test video ID extraction from various URL formats."""
        url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        url2 = "https://youtu.be/dQw4w9WgXcQ"
        url3 = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        
        vid1 = self.parser._extract_video_id(url1)
        vid2 = self.parser._extract_video_id(url2)
        vid3 = self.parser._extract_video_id(url3)
        
        assert vid1 == "dQw4w9WgXcQ"
        assert vid2 == "dQw4w9WgXcQ"
        assert vid3 == "dQw4w9WgXcQ"
        
    def test_parse_youtube_rss(self):
        """Test parsing YouTube RSS feed."""
        rss_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Video</title>
                <link href="https://www.youtube.com/watch?v=test123"/>
                <published>2024-01-01T00:00:00Z</published>
                <author><name>Test Channel</name></author>
                <media:group>
                    <media:description>Test video description</media:description>
                </media:group>
            </entry>
        </feed>
        """
        
        result = self.parser.parse(rss_content, "https://www.youtube.com/feeds/videos.xml?channel_id=test")
        
        assert isinstance(result, ParserResult)
        assert result.content_type == "youtube"
        assert result.custom_metadata["platform"] == "youtube"


class TestLinkedInParser:
    """Test LinkedIn parser."""
    
    def setup_method(self):
        self.parser = LinkedInParser()
        
    def test_parse_linkedin_content(self):
        """Test parsing LinkedIn HTML content."""
        html_content = b"""
        <html>
            <head><title>Company Page</title></head>
            <body>
                <h1 class="org-top-card-summary__title">Test Company</h1>
                <p class="org-top-card-summary__tagline">We build great software</p>
            </body>
        </html>
        """
        
        result = self.parser.parse(html_content, "https://linkedin.com/company/test")
        
        assert isinstance(result, ParserResult)
        assert result.content_type == "linkedin"
        assert result.custom_metadata["platform"] == "linkedin"
        assert "Test Company" in result.cleaned_text or result.title == "Test Company"
        
    def test_extract_title_from_html(self):
        """Test title extraction from HTML."""
        from bs4 import BeautifulSoup
        
        html = '<html><h1 class="org-top-card-summary__title">My Company</h1></html>'
        soup = BeautifulSoup(html, 'html.parser')
        
        title = self.parser._extract_title(soup)
        
        assert title == "My Company"
