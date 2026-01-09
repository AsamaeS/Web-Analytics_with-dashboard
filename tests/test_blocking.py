"""
Tests for blocking detection system.
Tests HTTP blocks, CAPTCHA detection, and IP ban detection.
"""

import pytest
from src.crawler.blocking_detector import BlockingDetector


class TestBlockingDetector:
    """Test blocking detection mechanisms."""
    
    def setup_method(self):
        self.detector = BlockingDetector()
        
    def test_http_403_detection(self):
        """Test HTTP 403 Forbidden detection."""
        block_type = self.detector.detect_http_block(403)
        
        assert block_type == "HTTP_403_FORBIDDEN"
        
    def test_http_429_detection(self):
        """Test HTTP 429 Rate Limit detection."""
        block_type = self.detector.detect_http_block(429)
        
        assert block_type == "HTTP_429_RATE_LIMIT"
        
    def test_http_503_detection(self):
        """Test HTTP 503 Service Unavailable detection."""
        block_type = self.detector.detect_http_block(503)
        
        assert block_type == "HTTP_503_SERVICE_UNAVAILABLE"
        
    def test_normal_status_codes(self):
        """Test that normal status codes don't trigger blocks."""
        assert self.detector.detect_http_block(200) is None
        assert self.detector.detect_http_block(301) is None
        assert self.detector.detect_http_block(404) is None
        
    def test_captcha_detection_in_text(self):
        """Test CAPTCHA detection in HTML content."""
        html_with_captcha = b"""
        <html>
            <body>
                <h1>Security Check</h1>
                <p>Please verify you are human by solving this CAPTCHA</p>
                <div class="g-recaptcha"></div>
            </body>
        </html>
        """
        
        is_captcha = self.detector.detect_captcha(html_with_captcha, "http://example.com")
        
        assert is_captcha is True
        
    def test_captcha_detection_cloudflare(self):
        """Test Cloudflare challenge detection."""
        html_cloudflare = b"""
        <html>
            <body>
                <div id="cf-wrapper">
                    <h1>Checking your browser</h1>
                </div>
            </body>
        </html>
        """
        
        is_captcha = self.detector.detect_captcha(html_cloudflare, "http://example.com")
        
        assert is_captcha is True
        
    def test_normal_content_no_captcha(self):
        """Test that normal content doesn't trigger CAPTCHA detection."""
        normal_html = b"""
        <html>
            <body>
                <h1>Welcome to our website</h1>
                <p>This is normal content about capturing data.</p>
            </body>
        </html>
        """
        
        is_captcha = self.detector.detect_captcha(normal_html, "http://example.com")
        
        assert is_captcha is False
        
    def test_ip_ban_http_429(self):
        """Test IP ban detection from HTTP 429."""
        content = b"Rate limit exceeded"
        
        is_banned = self.detector.detect_ip_ban(content, 429)
        
        assert is_banned is True
        
    def test_ip_ban_text_patterns(self):
        """Test IP ban detection from text patterns."""
        banned_content = b"""
        <html>
            <body>
                <h1>Access Denied</h1>
                <p>Your IP address has been temporarily blocked due to too many requests.</p>
            </body>
        </html>
        """
        
        is_banned = self.detector.detect_ip_ban(banned_content, 403)
        
        assert is_banned is True
        
    def test_normal_content_no_ban(self):
        """Test that normal content doesn't trigger IP ban detection."""
        normal_content = b"""
        <html>
            <body>
                <h1>Welcome</h1>
                <p>Normal content about access control and limits.</p>
            </body>
        </html>
        """
        
        is_banned = self.detector.detect_ip_ban(normal_content, 200)
        
        assert is_banned is False
        
    def test_detect_all_http_block(self):
        """Test comprehensive detection with HTTP block."""
        content = b"Forbidden"
        status_code = 403
        url = "http://example.com"
        
        result = self.detector.detect_all(content, status_code, url)
        
        assert result["blocked"] is True
        assert result["block_type"] == "HTTP_403_FORBIDDEN"
        assert result["http_block"] == "HTTP_403_FORBIDDEN"
        assert result["status_code"] == 403
        
    def test_detect_all_captcha(self):
        """Test comprehensive detection with CAPTCHA."""
        content = b'<html><div id="recaptcha">Verify you are human</div></html>'
        status_code = 200
        url = "http://example.com"
        
        result = self.detector.detect_all(content, status_code, url)
        
        assert result["blocked"] is True
        assert result["captcha_detected"] is True
        assert result["block_type"] == "CAPTCHA"
        
    def test_detect_all_ip_ban(self):
        """Test comprehensive detection with IP ban."""
        content = b"Your IP has been banned due to excessive requests"
        status_code = 403
        url = "http://example.com"
        
        result = self.detector.detect_all(content, status_code, url)
        
        assert result["blocked"] is True
        assert result["ip_ban_detected"] is True
        # Could be HTTP_403 or IP_BAN depending on detection order
        assert result["block_type"] in ["HTTP_403_FORBIDDEN", "IP_BAN"]
        
    def test_detect_all_no_blocking(self):
        """Test comprehensive detection with normal content."""
        content = b"<html><body>Normal webpage content</body></html>"
        status_code = 200
        url = "http://example.com"
        
        result = self.detector.detect_all(content, status_code, url)
        
        assert result["blocked"] is False
        assert result["block_type"] is None
        assert result["http_block"] is None
        assert result["captcha_detected"] is False
        assert result["ip_ban_detected"] is False
        
    def test_multiple_blocking_indicators(self):
        """Test detection when multiple blocking indicators are present."""
        content = b"""
        <html>
            <body>
                <h1>Rate limit exceeded</h1>
                <p>Please complete the CAPTCHA to continue</p>
                <div class="g-recaptcha"></div>
            </body>
        </html>
        """
        status_code = 429
        url = "http://example.com"
        
        result = self.detector.detect_all(content, status_code, url)
        
        assert result["blocked"] is True
        assert result["http_block"] == "HTTP_429_RATE_LIMIT"
        assert result["captcha_detected"] is True
        assert result["ip_ban_detected"] is True
        # Should have a block type (first detected)
        assert result["block_type"] is not None
