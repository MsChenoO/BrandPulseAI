# Phase 3/4: Search Router
# Full-text search using Elasticsearch + Semantic search using pgvector

from fastapi import APIRouter, Depends, HTTPException
from elasticsearch import Elasticsearch
from typing import List
import sys
import os
import time
from sqlmodel import Session, select, and_

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import (
    SearchRequest, SearchResponse, MentionResponse,
    SemanticSearchRequest, SemanticSearchResponse, SemanticMentionResponse,
    HybridSearchRequest, HybridSearchResponse, HybridMentionResponse
)
from api.dependencies import get_elasticsearch
from shared.elasticsearch_client import ElasticsearchClient, MENTIONS_INDEX
from shared.embedding_service import EmbeddingService
from models.database import get_engine, Mention, Brand

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


# ============================================================================
# Phase 4: POST /search/semantic - Semantic similarity search
# ============================================================================

@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic similarity search using embeddings",
    description="""
    Performs semantic similarity search using 768-dimensional embeddings.

    Features:
    - Converts query to embedding using Ollama
    - Finds semantically similar mentions using cosine similarity
    - Supports filtering by brand, source, sentiment
    - Returns similarity scores (0.0-1.0)
    - Configurable similarity threshold
    """
)
async def semantic_search(
    search_request: SemanticSearchRequest
) -> SemanticSearchResponse:
    """
    Search mentions using semantic similarity (embeddings + pgvector).

    Args:
        search_request: Semantic search query and filters

    Returns:
        Semantically similar mentions ranked by cosine similarity
    """
    start_time = time.time()

    # Initialize services
    embedding_service = EmbeddingService()
    engine = get_engine()

    # Generate embedding for query
    query_embedding = await embedding_service.generate_embedding(search_request.query)

    if not query_embedding:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embedding for query. Make sure Ollama is running."
        )

    # Build filters
    filters = [Mention.embedding.isnot(None)]  # Only mentions with embeddings

    if search_request.brand_id:
        filters.append(Mention.brand_id == search_request.brand_id)

    if search_request.source:
        filters.append(Mention.source == search_request.source)

    if search_request.sentiment:
        filters.append(Mention.sentiment_label == search_request.sentiment)

    # Execute vector similarity search using pgvector
    with Session(engine) as session:
        # Use pgvector's cosine distance operator (<=>)
        # Cosine distance: 0 = identical, 2 = opposite
        # Cosine similarity = 1 - (distance / 2)
        query = (
            select(
                Mention,
                Brand,
                # Calculate similarity: 1 - cosine_distance
                (1 - Mention.embedding.cosine_distance(query_embedding)).label('similarity')
            )
            .join(Brand, Mention.brand_id == Brand.id)
            .where(and_(*filters))
            .order_by(Mention.embedding.cosine_distance(query_embedding))
            .limit(search_request.limit)
        )

        results = session.exec(query).all()

        # Filter by similarity threshold and convert to response format
        mentions = []
        for mention, brand, similarity in results:
            # Skip if below threshold
            if similarity < search_request.similarity_threshold:
                continue

            mention_response = SemanticMentionResponse(
                id=mention.id,
                brand_id=mention.brand_id,
                brand_name=brand.name,
                source=mention.source,
                title=mention.title,
                url=mention.url,
                content=mention.content,
                sentiment_score=mention.sentiment_score,
                sentiment_label=mention.sentiment_label,
                published_date=mention.published_date,
                ingested_date=mention.ingested_date,
                processed_date=mention.processed_date,
                author=mention.author,
                points=mention.points,
                similarity_score=float(similarity)
            )
            mentions.append(mention_response)

    took_ms = int((time.time() - start_time) * 1000)

    return SemanticSearchResponse(
        results=mentions,
        total=len(mentions),
        query=search_request.query,
        took_ms=took_ms
    )


# ============================================================================
# Phase 4: POST /search/hybrid - Hybrid search (keyword + semantic)
# ============================================================================

@router.post(
    "/hybrid",
    response_model=HybridSearchResponse,
    summary="Hybrid search combining keyword and semantic similarity",
    description="""
    Combines Elasticsearch keyword search with pgvector semantic search.

    Features:
    - Runs both keyword and semantic search in parallel
    - Merges results using weighted scoring
    - Configurable semantic weight (0.0 = keyword only, 1.0 = semantic only)
    - Removes duplicates, keeping best score
    - Returns combined relevance scores
    """
)
async def hybrid_search(
    search_request: HybridSearchRequest,
    es: Elasticsearch = Depends(get_elasticsearch)
) -> HybridSearchResponse:
    """
    Hybrid search combining keyword (Elasticsearch) and semantic (pgvector) search.

    Args:
        search_request: Hybrid search query and parameters
        es: Elasticsearch client

    Returns:
        Merged search results with combined relevance scores
    """
    start_time = time.time()

    # Initialize services
    embedding_service = EmbeddingService()
    es_client = ElasticsearchClient()
    engine = get_engine()

    # Extract parameters
    query = search_request.query
    limit = search_request.limit
    semantic_weight = search_request.semantic_weight
    keyword_weight = 1.0 - semantic_weight

    # ========================================================================
    # 1. Keyword Search (Elasticsearch)
    # ========================================================================
    keyword_results = {}  # mention_id -> (score, mention_data)

    if keyword_weight > 0:
        es_results = es_client.search_mentions(
            query=query,
            brand_id=search_request.brand_id,
            source=search_request.source,
            sentiment=search_request.sentiment,
            limit=limit * 2,  # Get more results for merging
            index_name=MENTIONS_INDEX
        )

        # Normalize keyword scores to 0-1 range
        max_keyword_score = max([hit["_score"] for hit in es_results["hits"]], default=1.0)

        for hit in es_results["hits"]:
            mention_id = hit["_source"]["mention_id"]
            normalized_score = hit["_score"] / max_keyword_score if max_keyword_score > 0 else 0
            keyword_results[mention_id] = (normalized_score, hit["_source"])

    # ========================================================================
    # 2. Semantic Search (pgvector)
    # ========================================================================
    semantic_results = {}  # mention_id -> (similarity, mention)

    if semantic_weight > 0:
        query_embedding = await embedding_service.generate_embedding(query)

        if query_embedding:
            filters = [Mention.embedding.isnot(None)]

            if search_request.brand_id:
                filters.append(Mention.brand_id == search_request.brand_id)

            if search_request.source:
                filters.append(Mention.source == search_request.source)

            if search_request.sentiment:
                filters.append(Mention.sentiment_label == search_request.sentiment)

            with Session(engine) as session:
                query_stmt = (
                    select(
                        Mention,
                        Brand,
                        (1 - Mention.embedding.cosine_distance(query_embedding)).label('similarity')
                    )
                    .join(Brand, Mention.brand_id == Brand.id)
                    .where(and_(*filters))
                    .order_by(Mention.embedding.cosine_distance(query_embedding))
                    .limit(limit * 2)
                )

                results = session.exec(query_stmt).all()

                for mention, brand, similarity in results:
                    if similarity >= search_request.similarity_threshold:
                        semantic_results[mention.id] = (float(similarity), mention, brand)

    # ========================================================================
    # 3. Merge Results (Hybrid Scoring)
    # ========================================================================
    merged_results = {}  # mention_id -> (hybrid_score, mention_data, keyword_score, semantic_score)

    # Add keyword results
    for mention_id, (keyword_score, es_data) in keyword_results.items():
        hybrid_score = keyword_score * keyword_weight
        merged_results[mention_id] = {
            'hybrid_score': hybrid_score,
            'keyword_score': keyword_score,
            'semantic_score': None,
            'data': es_data,
            'mention': None
        }

    # Add/merge semantic results
    for mention_id, (semantic_score, mention, brand) in semantic_results.items():
        if mention_id in merged_results:
            # Already have keyword result - merge scores
            merged_results[mention_id]['semantic_score'] = semantic_score
            merged_results[mention_id]['hybrid_score'] += semantic_score * semantic_weight
        else:
            # New result from semantic only
            hybrid_score = semantic_score * semantic_weight
            merged_results[mention_id] = {
                'hybrid_score': hybrid_score,
                'keyword_score': None,
                'semantic_score': semantic_score,
                'data': None,
                'mention': mention,
                'brand': brand
            }

    # Sort by hybrid score and take top results
    sorted_results = sorted(
        merged_results.items(),
        key=lambda x: x[1]['hybrid_score'],
        reverse=True
    )[:limit]

    # Convert to response format
    hybrid_mentions = []
    for mention_id, result_data in sorted_results:
        # Use Elasticsearch data if available, otherwise database data
        if result_data['data']:
            es_data = result_data['data']
            mention_response = HybridMentionResponse(
                id=es_data["mention_id"],
                brand_id=es_data["brand_id"],
                brand_name=es_data.get("brand_name"),
                source=es_data["source"],
                title=es_data["title"],
                url=es_data["url"],
                content=es_data.get("content"),
                sentiment_score=es_data.get("sentiment_score"),
                sentiment_label=es_data.get("sentiment_label"),
                published_date=es_data.get("published_date"),
                ingested_date=es_data.get("ingested_date"),
                processed_date=es_data.get("processed_date"),
                author=es_data.get("author"),
                points=es_data.get("points"),
                hybrid_score=result_data['hybrid_score'],
                keyword_score=result_data['keyword_score'],
                semantic_score=result_data['semantic_score']
            )
        else:
            # Use database data
            mention = result_data['mention']
            brand = result_data['brand']
            mention_response = HybridMentionResponse(
                id=mention.id,
                brand_id=mention.brand_id,
                brand_name=brand.name,
                source=mention.source,
                title=mention.title,
                url=mention.url,
                content=mention.content,
                sentiment_score=mention.sentiment_score,
                sentiment_label=mention.sentiment_label,
                published_date=mention.published_date,
                ingested_date=mention.ingested_date,
                processed_date=mention.processed_date,
                author=mention.author,
                points=mention.points,
                hybrid_score=result_data['hybrid_score'],
                keyword_score=result_data['keyword_score'],
                semantic_score=result_data['semantic_score']
            )

        hybrid_mentions.append(mention_response)

    took_ms = int((time.time() - start_time) * 1000)

    return HybridSearchResponse(
        results=hybrid_mentions,
        total=len(hybrid_mentions),
        query=query,
        took_ms=took_ms,
        semantic_weight=semantic_weight
    )
