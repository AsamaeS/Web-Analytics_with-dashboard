"""
Blocking detection module.
Detects HTTP blocks (403, 429), CAPTCHAs, and IP bans.
"""

from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BlockingDetector:
    """Detects various types of blocking mechanisms."""
    
    # HTTP status codes indicating blocking
    BLOCK_STATUS_CODES = {403, 429, 503}
    
    # CAPTCHA indicators
    CAPTCHA_PATTERNS = [
        r'captcha',
        r'recaptcha',
        r'hcaptcha',
        r'cloudflare',
        r'challenge',
        r'verify you are human',
        r'security check',
        r'unusual traffic',
        r'robot',
        r'automated',
    ]
    
    # IP ban indicators
    IP_BAN_PATTERNS = [
        r'ip.*banned',
        r'ip.*blocked',
        r'access denied',
        r'forbidden',
        r'too many requests',
        r'rate limit exceeded',
        r'temporarily blocked',
    ]
    
    def __init__(self):
        self.captcha_regex = re.compile('|'.join(self.CAPTCHA_PATTERNS), re.IGNORECASE)
        self.ip_ban_regex = re.compile('|'.join(self.IP_BAN_PATTERNS), re.IGNORECASE)
        
    def detect_http_block(self, status_code: int) -> Optional[str]:
        """
        Detect HTTP-level blocking.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            Block type or None
        """
        if status_code == 403:
            return "HTTP_403_FORBIDDEN"
        elif status_code == 429:
            return "HTTP_429_RATE_LIMIT"
        elif status_code == 503:
            return "HTTP_503_SERVICE_UNAVAILABLE"
        elif status_code in self.BLOCK_STATUS_CODES:
            return f"HTTP_{status_code}_BLOCKED"
        return None
        
    def detect_captcha(self, content: bytes, url: str) -> bool:
        """
        Detect CAPTCHA challenges in HTML content.
        
        Args:
            content: HTML content
            url: Page URL
            
        Returns:
            True if CAPTCHA detected
        """
        try:
            html = content.decode('utf-8', errors='ignore')
            
            # Check for CAPTCHA patterns in text
            if self.captcha_regex.search(html):
                logger.warning(f"CAPTCHA detected in content from {url}")
                return True
                
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for CAPTCHA-specific elements
            captcha_indicators = [
                soup.find('iframe', src=re.compile(r'recaptcha|hcaptcha', re.I)),
                soup.find('div', {'class': re.compile(r'captcha|recaptcha|hcaptcha', re.I)}),
                soup.find('div', {'id': re.compile(r'captcha|recaptcha|hcaptcha', re.I)}),
                soup.find('form', action=re.compile(r'captcha', re.I)),
            ]
            
            if any(captcha_indicators):
                logger.warning(f"CAPTCHA element detected from {url}")
                return True
                
            # Check for Cloudflare challenge
            if soup.find('div', {'id': 'cf-wrapper'}):
                logger.warning(f"Cloudflare challenge detected from {url}")
                return True
                
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            
        return False
        
    def detect_ip_ban(self, content: bytes, status_code: int) -> bool:
        """
        Detect IP ban or rate limiting.
        
        Args:
            content: Response content
            status_code: HTTP status code
            
        Returns:
            True if IP ban detected
        """
        # Status code check
        if status_code == 429:
            logger.warning("HTTP 429 - Rate limit exceeded")
            return True
            
        try:
            text = content.decode('utf-8', errors='ignore')
            
            # Check for IP ban patterns
            if self.ip_ban_regex.search(text):
                logger.warning("IP ban pattern detected in response")
                return True
                
        except Exception as e:
            logger.error(f"Error detecting IP ban: {e}")
            
        return False
        
    def detect_all(
        self,
        content: bytes,
        status_code: int,
        url: str
    ) -> Dict[str, Any]:
        """
        Run all blocking detection checks.
        
        Args:
            content: Response content
            status_code: HTTP status code
            url: Request URL
            
        Returns:
            Dictionary with detection results
        """
        results = {
            "blocked": False,
            "block_type": None,
            "http_block": None,
            "captcha_detected": False,
            "ip_ban_detected": False,
            "status_code": status_code
        }
        
        # HTTP blocking
        http_block = self.detect_http_block(status_code)
        if http_block:
            results["blocked"] = True
            results["http_block"] = http_block
            results["block_type"] = http_block
            
        # CAPTCHA detection
        if self.detect_captcha(content, url):
            results["blocked"] = True
            results["captcha_detected"] = True
            results["block_type"] = results["block_type"] or "CAPTCHA"
            
        # IP ban detection
        if self.detect_ip_ban(content, status_code):
            results["blocked"] = True
            results["ip_ban_detected"] = True
            results["block_type"] = results["block_type"] or "IP_BAN"
            
        if results["blocked"]:
            logger.warning(
                f"Blocking detected for {url}: "
                f"type={results['block_type']}, "
                f"http={results['http_block']}, "
                f"captcha={results['captcha_detected']}, "
                f"ip_ban={results['ip_ban_detected']}"
            )
            
        return results


# Global instance
blocking_detector = BlockingDetector()
