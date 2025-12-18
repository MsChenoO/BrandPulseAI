# Phase 3: Elasticsearch Client and Utilities
# Handles indexing mentions and searching

from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


# ============================================================================
# Constants
# ============================================================================

MENTIONS_INDEX = "mentions"  # Index name for mentions


# ============================================================================
# Index Mapping (Schema)
# ============================================================================

MENTIONS_MAPPING = {
    "mappings": {
        "properties": {
            # IDs
            "mention_id": {"type": "integer"},
            "brand_id": {"type": "integer"},
            "brand_name": {"type": "keyword"},  # Exact match

            # Content (full-text search)
            "title": {
                "type": "text",
                "analyzer": "english",  # Stemming, stop words
                "fields": {
                    "keyword": {"type": "keyword"}  # Exact match version
                }
            },
            "content": {
                "type": "text",
                "analyzer": "english"
            },
            "url": {"type": "keyword"},  # No analysis needed

            # Metadata
            "source": {"type": "keyword"},  # google_news, hackernews
            "author": {"type": "keyword"},
            "points": {"type": "integer"},

            # Sentiment
            "sentiment_score": {"type": "float"},
            "sentiment_label": {"type": "keyword"},  # Positive, Neutral, Negative

            # Dates
            "published_date": {"type": "date"},
            "ingested_date": {"type": "date"},
            "processed_date": {"type": "date"},
            "indexed_date": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 1,  # Single node setup
        "number_of_replicas": 0  # No replicas for dev
    }
}


# ============================================================================
# Elasticsearch Client
# ============================================================================

class ElasticsearchClient:
    """Handles all Elasticsearch operations for mentions"""

    def __init__(self, es_url: Optional[str] = None):
        """
        Initialize Elasticsearch client.

        Args:
            es_url: Elasticsearch URL (default: from env or localhost)
        """
        if es_url is None:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

        self.es = Elasticsearch([es_url])
        self.es_url = es_url

    def create_index(self, index_name: str = MENTIONS_INDEX) -> bool:
        """
        Create the mentions index with proper mapping.

        Args:
            index_name: Name of the index to create

        Returns:
            True if created, False if already exists
        """
        try:
            if self.es.indices.exists(index=index_name):
                print(f"Index '{index_name}' already exists")
                return False

            # Create index with mapping
            self.es.indices.create(
                index=index_name,
                mappings=MENTIONS_MAPPING["mappings"],
                settings=MENTIONS_MAPPING["settings"]
            )
            print(f"✓ Created index: {index_name}")
            return True

        except Exception as e:
            print(f"Error creating index: {e}")
            return False

    def delete_index(self, index_name: str = MENTIONS_INDEX) -> bool:
        """
        Delete an index (use carefully!).

        Args:
            index_name: Name of the index to delete

        Returns:
            True if deleted successfully
        """
        try:
            if not self.es.indices.exists(index=index_name):
                print(f"Index '{index_name}' does not exist")
                return False

            self.es.indices.delete(index=index_name)
            print(f"✓ Deleted index: {index_name}")
            return True

        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def index_mention(
        self,
        mention_data: Dict[str, Any],
        index_name: str = MENTIONS_INDEX
    ) -> Optional[str]:
        """
        Index a single mention document.

        Args:
            mention_data: Mention data to index
            index_name: Target index name

        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Add indexed timestamp
            mention_data["indexed_date"] = datetime.utcnow()

            # Index document (use mention_id as document ID for deduplication)
            doc_id = mention_data.get("mention_id")

            response = self.es.index(
                index=index_name,
                id=doc_id,  # Use mention_id as ES document ID
                document=mention_data
            )

            return response["_id"]

        except Exception as e:
            print(f"Error indexing mention: {e}")
            return None

    def bulk_index_mentions(
        self,
        mentions: List[Dict[str, Any]],
        index_name: str = MENTIONS_INDEX
    ) -> int:
        """
        Index multiple mentions in bulk (more efficient).

        Args:
            mentions: List of mention documents
            index_name: Target index name

        Returns:
            Number of documents successfully indexed
        """
        from elasticsearch.helpers import bulk

        try:
            # Prepare bulk actions
            actions = []
            for mention in mentions:
                mention["indexed_date"] = datetime.utcnow()

                action = {
                    "_index": index_name,
                    "_id": mention.get("mention_id"),
                    "_source": mention
                }
                actions.append(action)

            # Execute bulk indexing
            success, failed = bulk(self.es, actions, raise_on_error=False)

            if failed:
                print(f"Failed to index {len(failed)} documents")

            return success

        except Exception as e:
            print(f"Error bulk indexing: {e}")
            return 0

    def search_mentions(
        self,
        query: str,
        brand_id: Optional[int] = None,
        source: Optional[str] = None,
        sentiment: Optional[str] = None,
        limit: int = 20,
        index_name: str = MENTIONS_INDEX
    ) -> Dict[str, Any]:
        """
        Search mentions with filters.

        Args:
            query: Search query text
            brand_id: Filter by brand ID
            source: Filter by source (google_news, hackernews)
            sentiment: Filter by sentiment label
            limit: Maximum results
            index_name: Index to search

        Returns:
            Search results with hits and metadata
        """
        try:
            # Build query
            must_clauses = []
            filter_clauses = []

            # Full-text search on title and content
            if query:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content"],  # Title is 2x important
                        "type": "best_fields",
                        "fuzziness": "AUTO"  # Handle typos
                    }
                })

            # Filters
            if brand_id is not None:
                filter_clauses.append({"term": {"brand_id": brand_id}})

            if source:
                filter_clauses.append({"term": {"source": source}})

            if sentiment:
                filter_clauses.append({"term": {"sentiment_label": sentiment}})

            # Construct full query
            es_query = {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses
                }
            }

            # Execute search
            response = self.es.search(
                index=index_name,
                query=es_query,
                size=limit,
                highlight={
                    "fields": {
                        "title": {},
                        "content": {}
                    }
                },
                sort=[
                    {"_score": {"order": "desc"}},  # Relevance first
                    {"published_date": {"order": "desc"}}  # Then recency
                ]
            )

            return {
                "hits": response["hits"]["hits"],
                "total": response["hits"]["total"]["value"],
                "took_ms": response["took"]
            }

        except Exception as e:
            print(f"Error searching: {e}")
            return {"hits": [], "total": 0, "took_ms": 0}

    def get_mention_by_id(
        self,
        mention_id: int,
        index_name: str = MENTIONS_INDEX
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific mention by ID.

        Args:
            mention_id: Mention ID
            index_name: Index name

        Returns:
            Mention document if found, None otherwise
        """
        try:
            response = self.es.get(
                index=index_name,
                id=mention_id
            )
            return response["_source"]

        except Exception as e:
            print(f"Error getting mention: {e}")
            return None

    def close(self):
        """Close Elasticsearch connection"""
        self.es.close()


# ============================================================================
# Helper Functions
# ============================================================================

def initialize_elasticsearch():
    """
    Initialize Elasticsearch index (call at startup).

    Creates the mentions index if it doesn't exist.
    """
    client = ElasticsearchClient()
    client.create_index()
    client.close()


def convert_mention_to_es_doc(mention_db) -> Dict[str, Any]:
    """
    Convert a SQLModel Mention object to Elasticsearch document.

    Args:
        mention_db: Mention object from database

    Returns:
        Dictionary ready for indexing
    """
    return {
        "mention_id": mention_db.id,
        "brand_id": mention_db.brand_id,
        "brand_name": mention_db.brand.name if hasattr(mention_db, 'brand') else None,
        "title": mention_db.title,
        "content": mention_db.content,
        "url": mention_db.url,
        "source": mention_db.source,
        "author": mention_db.author,
        "points": mention_db.points,
        "sentiment_score": mention_db.sentiment_score,
        "sentiment_label": mention_db.sentiment_label,
        "published_date": mention_db.published_date,
        "ingested_date": mention_db.ingested_date,
        "processed_date": mention_db.processed_date
    }
