"""
Web Crawler & Reporting Platform - Main Entry Point
"""

import sys
import os
import socket
from contextlib import closing

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import uvicorn
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def check_port_available(host: str, port: int) -> bool:
    """Check if a port is available."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def main():
    """Main application entry point."""
    try:
        logger.info("=" * 80)
        logger.info("Starting Web Crawler & Reporting Platform...")
        logger.info("=" * 80)
        
        # Check port availability
        host = settings.api_host
        port = settings.api_port
        
        if not check_port_available(host, port):
            logger.error(f"Port {port} is already in use!")
            logger.error(f"Please stop the existing process or change API_PORT in .env")
            logger.error(f"To find process: netstat -ano | findstr :{port}")
            sys.exit(1)
        
        logger.info(f"API will be available at http://{host}:{port}")
        logger.info(f"Dashboard: http://localhost:{port}/")
        logger.info(f"API Docs: http://localhost:{port}/docs")
        logger.info("=" * 80)
        
        # Start server
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=False,  # Disable reload to prevent duplicate starts
            log_level=settings.log_level.lower()
        )
        
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
