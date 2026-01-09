"""
MongoDB connection and database operations.
Provides connection management, CRUD operations, and search functionality.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId

from ..utils.config import settings
from ..utils.logger import setup_logger
from .models import (
    Source, Document, ContentType, CrawlStatus,
    SearchQuery, SearchResult, CrawlStats
)

logger = setup_logger(__name__, level=settings.log_level)


class MongoDBManager:
    """MongoDB connection and operations manager."""
    
    def __init__(self, uri: str = None, db_name: str = None):
        """
        Initialize MongoDB connection.
        
        Args:
            uri: MongoDB connection URI (defaults to settings)
            db_name: Database name (defaults to settings)
        """
        self.uri = uri or settings.mongodb_uri
        self.db_name = db_name or settings.mongodb_db
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connected = False
        
    def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self._connected = True
            logger.info(f"Connected to MongoDB database: {self.db_name}")
            
            # Initialize collections and indexes
            self._initialize_collections()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
            
    def _initialize_collections(self) -> None:
        """Create collections and indexes."""
        # Sources collection
        sources_coll = self.db.sources
        sources_coll.create_index([("url", ASCENDING)], unique=True)
        sources_coll.create_index([("created_at", DESCENDING)])
        sources_coll.create_index([("status", ASCENDING)])
        
        # Documents collection
        documents_coll = self.db.documents
        documents_coll.create_index([("url", ASCENDING), ("source_id", ASCENDING)], unique=True)
        documents_coll.create_index([("source_id", ASCENDING)])
        documents_coll.create_index([("crawled_at", DESCENDING)])
        documents_coll.create_index([("content_type", ASCENDING)])
        
        # Text index for full-text search on cleaned_text
        documents_coll.create_index([("cleaned_text", TEXT)])
        
        # Crawl stats collection
        stats_coll = self.db.crawl_stats
        stats_coll.create_index([("source_id", ASCENDING), ("started_at", DESCENDING)])
        
        # Projects collection
        projects_coll = self.db.projects
        projects_coll.create_index([("name", ASCENDING)])
        projects_coll.create_index([("domain", ASCENDING)])
        projects_coll.create_index([("created_at", DESCENDING)])
        
        logger.info("Initialized MongoDB collections and indexes")
        
    @property
    def sources(self) -> Collection:
        """Get sources collection."""
        return self.db.sources
        
    @property
    def documents(self) -> Collection:
        """Get documents collection."""
        return self.db.documents
        
    @property
    def crawl_stats(self) -> Collection:
        """Get crawl stats collection."""
        return self.db.crawl_stats
    
    @property
    def projects(self) -> Collection:
        """Get projects collection."""
        return self.db.projects
        
    # ========================
    # Project CRUD Operations
    # ========================
    
    def create_project(self, project) -> str:
        """Create a new project."""
        from .models import Project
        project_dict = project.model_dump(exclude={"id"})
        project_dict["created_at"] = datetime.utcnow()
        project_dict["updated_at"] = datetime.utcnow()
        
        result = self.projects.insert_one(project_dict)
        project_id = str(result.inserted_id)
        logger.info(f"Created project: {project.name} (ID: {project_id})")
        return project_id
    
    def get_project(self, project_id: str):
        """Get project by ID."""
        from .models import Project
        try:
            obj_id = ObjectId(project_id)
        except InvalidId:
            logger.error(f"Invalid project ID: {project_id}")
            return None
        
        doc = self.projects.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return Project(**doc)
        return None
    
    def list_projects(self, limit: int = 100):
        """List all projects."""
        from .models import Project
        cursor = self.projects.find().limit(limit).sort("created_at", DESCENDING)
        
        projects = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            projects.append(Project(**doc))
        return projects
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update project fields."""
        try:
            obj_id = ObjectId(project_id)
        except InvalidId:
            return False
        
        updates["updated_at"] = datetime.utcnow()
        result = self.projects.update_one({"_id": obj_id}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project and all associated sources."""
        try:
            obj_id = ObjectId(project_id)
        except InvalidId:
            return False
        
        # Delete all sources from this project
        source_result = self.sources.delete_many({"project_id": project_id})
        logger.info(f"Deleted {source_result.deleted_count} sources for project {project_id}")
        
        # Delete the project
        result = self.projects.delete_one({"_id": obj_id})
        if result.deleted_count > 0:
            logger.info(f"Deleted project {project_id}")
            return True
        return False
        
    # ========================
    # Source CRUD Operations
    # ========================
    
    def create_source(self, source: Source) -> str:
        """
        Create a new source.
        
        Args:
            source: Source model
            
        Returns:
            Inserted source ID
            
        Raises:
            DuplicateKeyError: If URL already exists
        """
        source_dict = source.model_dump(exclude={"id"})
        source_dict["created_at"] = datetime.utcnow()
        source_dict["updated_at"] = datetime.utcnow()
        
        try:
            result = self.sources.insert_one(source_dict)
            source_id = str(result.inserted_id)
            logger.info(f"Created source: {source.name} (ID: {source_id})")
            return source_id
        except DuplicateKeyError:
            logger.error(f"Source with URL {source.url} already exists")
            raise
            
    def get_source(self, source_id: str) -> Optional[Source]:
        """
        Get source by ID.
        
        Args:
            source_id: Source ID
            
        Returns:
            Source model or None if not found
        """
        try:
            obj_id = ObjectId(source_id)
        except InvalidId:
            logger.error(f"Invalid source ID: {source_id}")
            return None
            
        doc = self.sources.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return Source(**doc)
        return None
        
    def list_sources(
        self,
        status: Optional[CrawlStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Source]:
        """
        List sources with optional filtering.
        
        Args:
            status: Filter by crawl status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of source models
        """
        query = {}
        if status:
            query["status"] = status.value
            
        cursor = self.sources.find(query).skip(offset).limit(limit).sort("created_at", DESCENDING)
        
        sources = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            sources.append(Source(**doc))
            
        return sources
        
    def update_source(self, source_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update source fields.
        
        Args:
            source_id: Source ID
            updates: Dictionary of fields to update
            
        Returns:
            True if updated, False if not found
        """
        try:
            obj_id = ObjectId(source_id)
        except InvalidId:
            logger.error(f"Invalid source ID: {source_id}")
            return False
            
        updates["updated_at"] = datetime.utcnow()
        result = self.sources.update_one({"_id": obj_id}, {"$set": updates})
        
        if result.modified_count > 0:
            logger.info(f"Updated source {source_id}")
            return True
        return False
        
    def delete_source(self, source_id: str) -> bool:
        """
        Delete source and all its documents.
        
        Args:
            source_id: Source ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            obj_id = ObjectId(source_id)
        except InvalidId:
            logger.error(f"Invalid source ID: {source_id}")
            return False
            
        # Delete all documents from this source
        doc_result = self.documents.delete_many({"source_id": source_id})
        logger.info(f"Deleted {doc_result.deleted_count} documents for source {source_id}")
        
        # Delete the source
        result = self.sources.delete_one({"_id": obj_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted source {source_id}")
            return True
        return False
        
    # ========================
    # Document CRUD Operations
    # ========================
    
    def create_document(self, document: Document) -> Optional[str]:
        """
        Create a new document.
        
        Args:
            document: Document model
            
        Returns:
            Inserted document ID or None if duplicate
        """
        doc_dict = document.model_dump(exclude={"id"})
        doc_dict["metadata"] = document.metadata.model_dump()
        doc_dict["crawled_at"] = datetime.utcnow()
        
        try:
            result = self.documents.insert_one(doc_dict)
            doc_id = str(result.inserted_id)
            logger.debug(f"Created document: {document.url}")
            return doc_id
        except DuplicateKeyError:
            logger.warning(f"Document already exists: {document.url}")
            return None
            
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document model or None if not found
        """
        try:
            obj_id = ObjectId(document_id)
        except InvalidId:
            return None
            
        doc = self.documents.find_one({"_id": obj_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            return Document(**doc)
        return None
        
    def list_documents(
        self,
        source_id: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """
        List documents with optional filtering.
        
        Args:
            source_id: Filter by source ID
            content_type: Filter by content type
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of document models
        """
        query = {}
        if source_id:
            query["source_id"] = source_id
        if content_type:
            query["content_type"] = content_type.value
            
        cursor = self.documents.find(query).skip(offset).limit(limit).sort("crawled_at", DESCENDING)
        
        documents = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            documents.append(Document(**doc))
            
        return documents
        
    def count_documents(self, source_id: Optional[str] = None) -> int:
        """
        Count documents, optionally filtered by source.
        
        Args:
            source_id: Optional source ID filter
            
        Returns:
            Document count
        """
        query = {}
        if source_id:
            query["source_id"] = source_id
        return self.documents.count_documents(query)
        
    # ========================
    # Search Operations
    # ========================
    
    def search_documents(self, search_query: SearchQuery) -> List[SearchResult]:
        """
        Search documents using keyword-based full-text search.
        
        Args:
            search_query: Search query parameters
            
        Returns:
            List of search results with relevance scores
        """
        # Build MongoDB query
        query: Dict[str, Any] = {
            "$text": {"$search": search_query.keywords}
        }
        
        # Add filters
        if search_query.source_id:
            query["source_id"] = search_query.source_id
        if search_query.content_type:
            query["content_type"] = search_query.content_type.value
        if search_query.date_from or search_query.date_to:
            date_filter = {}
            if search_query.date_from:
                date_filter["$gte"] = search_query.date_from
            if search_query.date_to:
                date_filter["$lte"] = search_query.date_to
            query["crawled_at"] = date_filter
            
        # Execute search with text score for relevance
        cursor = self.documents.find(
            query,
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).skip(search_query.offset).limit(search_query.limit)
        
        results = []
        for doc in cursor:
            # Generate snippet with keyword context
            snippet = self._generate_snippet(
                doc.get("cleaned_text", ""),
                search_query.keywords
            )
            
            result = SearchResult(
                document_id=str(doc["_id"]),
                url=doc["url"],
                title=doc.get("metadata", {}).get("title"),
                snippet=snippet,
                relevance_score=doc.get("score", 0.0),
                source_id=doc["source_id"],
                content_type=doc["content_type"],
                crawled_at=doc["crawled_at"]
            )
            results.append(result)
            
        logger.info(f"Search for '{search_query.keywords}' returned {len(results)} results")
        return results
        
    def _generate_snippet(self, text: str, keywords: str, max_length: int = 200) -> str:
        """
        Generate a snippet from text with keyword context.
        
        Args:
            text: Full text
            keywords: Search keywords
            max_length: Maximum snippet length
            
        Returns:
            Text snippet
        """
        if not text:
            return ""
            
        # Simple keyword-based snippet extraction
        keywords_list = keywords.lower().split()
        text_lower = text.lower()
        
        # Find first occurrence of any keyword
        best_pos = -1
        for keyword in keywords_list:
            pos = text_lower.find(keyword)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
                    
        if best_pos == -1:
            # No keyword found, return beginning
            return text[:max_length] + ("..." if len(text) > max_length else "")
            
        # Extract snippet around keyword
        start = max(0, best_pos - max_length // 2)
        end = min(len(text), best_pos + max_length // 2)
        snippet = text[start:end]
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
            
        return snippet
        
    # ========================
    # Statistics Operations
    # ========================
    
    def save_crawl_stats(self, stats: CrawlStats) -> str:
        """
        Save crawl statistics.
        
        Args:
            stats: Crawl statistics
            
        Returns:
            Inserted stats ID
        """
        stats_dict = stats.model_dump()
        result = self.crawl_stats.insert_one(stats_dict)
        return str(result.inserted_id)
        
    def get_source_stats(self, source_id: str) -> Dict[str, Any]:
        """
        Get statistics for a source.
        
        Args:
            source_id: Source ID
            
        Returns:
            Statistics dictionary
        """
        total_docs = self.count_documents(source_id)
        
        # Get latest crawl stats
        latest_stats = self.crawl_stats.find_one(
            {"source_id": source_id},
            sort=[("started_at", DESCENDING)]
        )
        
        return {
            "source_id": source_id,
            "total_documents": total_docs,
            "latest_crawl": latest_stats
        }
        
    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global statistics across all sources.
        
        Returns:
            Statistics dictionary
        """
        total_sources = self.sources.count_documents({})
        total_documents = self.documents.count_documents({})
        
        # Documents per content type
        pipeline = [
            {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
        ]
        content_type_stats = list(self.documents.aggregate(pipeline))
        
        # Documents per source
        pipeline = [
            {"$group": {"_id": "$source_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_sources = list(self.documents.aggregate(pipeline))
        
        return {
            "total_sources": total_sources,
            "total_documents": total_documents,
            "by_content_type": content_type_stats,
            "top_sources": top_sources
        }


# Global MongoDB manager instance
db_manager = MongoDBManager()
