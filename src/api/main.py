"""
FastAPI application initialization.
Provides REST API for web crawler and reporting platform.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
import traceback

from ..storage import db_manager
from ..crawler.scheduler import crawl_scheduler
from ..utils.logger import setup_logger
from ..utils.config import settings

logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Web Crawler & Reporting Platform",
    description="Configurable web crawler with MongoDB storage and reporting dashboard",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    logger.debug(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Connect to MongoDB
        db_manager.connect()
        logger.info("MongoDB connected")
        
        # Start scheduler
        crawl_scheduler.start()
        logger.info("Crawler scheduler started")
        
        # Load existing source schedules
        count = crawl_scheduler.load_all_sources()
        logger.info(f"Loaded {count} scheduled crawl jobs")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        # Shutdown scheduler
        crawl_scheduler.shutdown(wait=True)
        logger.info("Crawler scheduler shut down")
        
        # Disconnect from MongoDB
        db_manager.disconnect()
        logger.info("MongoDB disconnected")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mongodb": db_manager._connected,
        "scheduler": crawl_scheduler.scheduler.running
    }


# Root endpoint
@app.get("/", response_class=HTMLResponse, tags=["System"])
async def root():
    """Serve dashboard."""
    dashboard_file = Path(__file__).parent.parent / "dashboard" / "templates" / "index.html"
    
    if dashboard_file.exists():
        return HTMLResponse(content=dashboard_file.read_text(encoding='utf-8'), status_code=200)
    else:
        return HTMLResponse(
            content="<h1>Web Crawler & Reporting Platform</h1><p>API is running. Dashboard not found.</p>",
            status_code=200
        )


# Mount static files
static_path = Path(__file__).parent.parent / "dashboard" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Import and include routers
from .sources import router as sources_router
from .crawler import router as crawler_router
from .search import router as search_router
from .reports import router as reports_router
from .decision import router as decision_router
from .projects import router as projects_router

app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(sources_router, prefix="/api/sources", tags=["Sources"])
app.include_router(crawler_router, prefix="/api/crawler", tags=["Crawler"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(decision_router, prefix="/api/decision", tags=["Decision Intelligence"])
