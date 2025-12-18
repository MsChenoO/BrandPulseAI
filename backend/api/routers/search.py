# Phase 3: Search Router
# Full-text search using Elasticsearch

from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import SearchRequest, SearchResponse, MentionResponse
from api.dependencies import get_elasticsearch
from shared.elasticsearch_client import ElasticsearchClient, MENTIONS_INDEX

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


# ============================================================================
# POST /search - Full-text search
# ============================================================================

@router.post(
    "",
    response_model=SearchResponse,
    summary="Search mentions using Elasticsearch",
    description="""
    Performs full-text search on mention titles and content.

    Features:
    - Multi-field search (title boosted 2x)
    - Fuzzy matching for typos
    - Filter by brand, source, sentiment
    - Relevance scoring
    - Highlighting of matched terms
    """
)
def search_mentions(
    search_request: SearchRequest,
    es: Elasticsearch = Depends(get_elasticsearch)
) -> SearchResponse:
    """
    Search mentions with full-text search and filters.

    Args:
        search_request: Search query and filters
        es: Elasticsearch client

    Returns:
        Search results with highlights and relevance scores
    """
    # Create Elasticsearch client wrapper (reuses the same URL from environment)
    es_client = ElasticsearchClient()

    # Extract search parameters
    query = search_request.query
    limit = search_request.limit or 20

    # Build filter parameters (directly from request)
    brand_id = search_request.brand_id
    source = search_request.source
    sentiment = search_request.sentiment

    # Execute search
    search_results = es_client.search_mentions(
        query=query,
        brand_id=brand_id,
        source=source,
        sentiment=sentiment,
        limit=limit,
        index_name=MENTIONS_INDEX
    )

    # Convert Elasticsearch results to response format
    mentions = []
    for hit in search_results["hits"]:
        source_data = hit["_source"]
        score = hit["_score"]
        highlights = hit.get("highlight", {})

        # Create MentionResponse from Elasticsearch document
        mention = MentionResponse(
            id=source_data["mention_id"],
            brand_id=source_data["brand_id"],
            brand_name=source_data.get("brand_name"),
            title=source_data["title"],
            content=source_data.get("content"),
            url=source_data["url"],
            source=source_data["source"],
            author=source_data.get("author"),
            points=source_data.get("points"),
            sentiment_score=source_data.get("sentiment_score"),
            sentiment_label=source_data.get("sentiment_label"),
            published_date=source_data.get("published_date"),
            ingested_date=source_data.get("ingested_date"),
            processed_date=source_data.get("processed_date"),
            # Add highlights if available
            highlights=highlights if highlights else None
        )
        mentions.append(mention)

    # Return search response
    return SearchResponse(
        results=mentions,
        total=search_results["total"],
        took_ms=search_results["took_ms"],
        query=query
    )


# ============================================================================
# GET /search/health - Check Elasticsearch connection
# ============================================================================

@router.get(
    "/health",
    summary="Check Elasticsearch health",
    description="Verifies that Elasticsearch is connected and the index exists."
)
def search_health(
    es: Elasticsearch = Depends(get_elasticsearch)
) -> dict:
    """
    Check Elasticsearch connection and index status.

    Args:
        es: Elasticsearch client

    Returns:
        Health status information
    """
    try:
        # Check if Elasticsearch is reachable
        es_info = es.info()

        # Check if mentions index exists (convert to bool explicitly)
        index_exists = bool(es.indices.exists(index=MENTIONS_INDEX))

        # Get index stats if it exists
        doc_count = 0
        if index_exists:
            stats = es.indices.stats(index=MENTIONS_INDEX)
            doc_count = stats["_all"]["primaries"]["docs"]["count"]

        return {
            "status": "healthy",
            "elasticsearch_version": es_info["version"]["number"],
            "cluster_name": es_info["cluster_name"],
            "index_exists": index_exists,
            "index_name": MENTIONS_INDEX,
            "document_count": doc_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Elasticsearch health check failed: {str(e)}"
        )
