"""
Reporting and export API endpoints.
Generates reports and exports data in various formats.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

from ..storage import db_manager, ContentType
from ..processing.text_cleaner import TextCleaner
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# Response models
class KeywordFrequencyItem(BaseModel):
    """Keyword frequency item."""
    keyword: str
    frequency: int


class SourceSummaryItem(BaseModel):
    """Source summary item."""
    source_id: str
    source_name: str
    document_count: int
    last_crawl: Optional[str]


class CrawlTimelineItem(BaseModel):
    """Crawl timeline item."""
    date: str
    crawl_count: int
    document_count: int


# Endpoints
@router.get("/keyword-frequency")
async def get_keyword_frequency(
    top_n: int = Query(20, ge=1, le=100, description="Number of top keywords"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date")
):
    """
    Get keyword frequency across documents.
    
    Args:
        top_n: Number of top keywords to return
        source_id: Optional source filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        
    Returns:
        List of keywords with frequencies
    """
    try:
        # Get documents
        documents = db_manager.list_documents(
            source_id=source_id,
            limit=1000  # Limit for performance
        )
        
        # Aggregate keyword frequencies
        text_cleaner = TextCleaner()
        all_keywords = []
        
        for doc in documents:
            # Filter by date if specified
            if date_from and doc.crawled_at < date_from:
                continue
            if date_to and doc.crawled_at > date_to:
                continue
                
            # Extract keywords
            keywords = text_cleaner.extract_keywords(doc.cleaned_text, top_n=50)
            all_keywords.extend(keywords)
            
        # Count frequencies
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        # Get top N
        top_keywords = [
            {"keyword": kw, "frequency": count}
            for kw, count in keyword_counts.most_common(top_n)
        ]
        
        return top_keywords
        
    except Exception as e:
        logger.error(f"Failed to generate keyword frequency report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/source-summary")
async def get_source_summary():
    """
    Get summary of documents per source.
    
    Returns:
        List of sources with document counts
    """
    try:
        sources = db_manager.list_sources(limit=1000)
        
        summary = [
            {
                "source_id": source.id,
                "source_name": source.name,
                "document_count": source.total_documents,
                "last_crawl": source.last_crawl.isoformat() if source.last_crawl else None
            }
            for source in sources
        ]
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate source summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/crawl-timeline")
async def get_crawl_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to include")
):
    """
    Get crawl activity timeline.
    
    Args:
        days: Number of days to include in timeline
        
    Returns:
        Timeline of crawl activity
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get crawl stats
        stats_list = list(db_manager.crawl_stats.find({
            "started_at": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Group by date
        timeline_dict: Dict[str, Dict[str, int]] = {}
        
        for stat in stats_list:
            date_key = stat["started_at"].date().isoformat()
            if date_key not in timeline_dict:
                timeline_dict[date_key] = {"crawl_count": 0, "documents_collected": 0}
            timeline_dict[date_key]["crawl_count"] += 1
            timeline_dict[date_key]["documents_collected"] += stat.get("pages_crawled", 0)
            
        # Convert to list
        timeline = [
            {
                "date": date_key,
                "crawl_count": data["crawl_count"],
                "documents_collected": data["documents_collected"]
            }
            for date_key, data in sorted(timeline_dict.items())
        ]
        
        return timeline
        
    except Exception as e:
        logger.error(f"Failed to generate crawl timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/content-type-distribution")
async def get_content_type_distribution():
    """
    Get distribution of documents by content type.
    
    Returns:
        Content type distribution
    """
    try:
        # Aggregate by content_type
        pipeline = [
            {"$group": {
                "_id": "$content_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(db_manager.documents.aggregate(pipeline))
        
        distribution = [
            {
                "content_type": item["_id"],
                "count": item["count"]
            }
            for item in results
        ]
        
        return distribution
        
    except Exception as e:
        logger.error(f"Failed to get content type distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/blocking-stats")
async def get_blocking_stats():
    """
    Get blocking statistics per source.
    
    Returns:
        Blocking statistics
    """
    try:
        sources = db_manager.list_sources(limit=1000)
        
        blocked = [s for s in sources if s.status == "blocked"]
        healthy = [s for s in sources if s.status in ["idle", "completed"]]
        running = [s for s in sources if s.status == "running"]
        failed = [s for s in sources if s.status == "failed"]
        
        return {
            "total": len(sources),
            "blocked": len(blocked),
            "healthy": len(healthy),
            "running": len(running),
            "failed": len(failed),
            "blocked_sources": [
                {
                    "name": s.name,
                    "content_type": s.content_type.value,
                    "error": s.last_error or "Unknown"
                }
                for s in blocked
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get blocking stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/csv")
async def export_csv(
    report_type: str = Query(..., pattern="^(keywords|sources|documents)$"),
    source_id: Optional[str] = Query(None)
):
    """
    Export report as CSV.
    
    Args:
        report_type: Type of report (keywords, sources, documents)
        source_id: Optional source filter
        
    Returns:
        CSV file
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == "keywords":
            # Export keyword frequency
            result = await get_keyword_frequency(top_n=100, source_id=source_id)
            writer.writerow(["Keyword", "Frequency"])
            for item in result:
                writer.writerow([item["keyword"], item["frequency"]])
                
        elif report_type == "sources":
            # Export source summary
            result = await get_source_summary()
            writer.writerow(["Source ID", "Source Name", "Document Count", "Last Crawl"])
            for item in result:
                writer.writerow([
                    item["source_id"],
                    item["source_name"],
                    item["document_count"],
                    item["last_crawl"] or "Never"
                ])
                
        elif report_type == "documents":
            # Export documents
            documents = db_manager.list_documents(source_id=source_id, limit=1000)
            writer.writerow(["URL", "Title", "Content Type", "Source ID", "Crawled At", "Word Count"])
            for doc in documents:
                writer.writerow([
                    doc.url,
                    doc.metadata.title or "Untitled",
                    doc.content_type.value,
                    doc.source_id,
                    doc.crawled_at.isoformat(),
                    doc.metadata.word_count
                ])
                
        csv_content = output.getvalue()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={report_type}_export.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/pdf")
async def export_pdf(
    report_type: str = Query(..., pattern="^(keywords|sources)$"),
    source_id: Optional[str] = Query(None)
):
    """
    Export report as PDF.
    
    Args:
        report_type: Type of report (keywords, sources)
        source_id: Optional source filter
        
    Returns:
        PDF file
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_text = f"{report_type.capitalize()} Report"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Timestamp
        timestamp = Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", styles['Normal'])
        elements.append(timestamp)
        elements.append(Spacer(1, 0.3 * inch))
        
        if report_type == "keywords":
            # Keyword frequency table
            result = await get_keyword_frequency(top_n=50, source_id=source_id)
            
            data = [["Keyword", "Frequency"]]
            for item in result:
                data.append([item["keyword"], str(item["frequency"])])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
        elif report_type == "sources":
            # Source summary table
            result = await get_source_summary()
            
            data = [["Source Name", "Documents", "Last Crawl"]]
            for item in result:
                data.append([
                    item["source_name"],
                    str(item["document_count"]),
                    item["last_crawl"] or "Never"
                ])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
        # Build PDF
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={report_type}_report.pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
