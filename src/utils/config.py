"""
Configuration management for the web crawler application.
Loads settings from environment variables with sensible defaults.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # MongoDB Configuration
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI"
    )
    mongodb_db: str = Field(
        default="web_crawler",
        description="MongoDB database name"
    )
    
    # Crawler Configuration
    crawler_user_agent: str = Field(
        default="WebCrawlerBot/1.0 (+https://example.com/bot)",
        description="User agent string for HTTP requests"
    )
    crawler_delay: float = Field(
        default=1.0,
        description="Delay between requests in seconds (politeness)"
    )
    max_workers: int = Field(
        default=5,
        description="Maximum number of concurrent crawl workers"
    )
    request_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Optional log file path"
    )
    
    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
