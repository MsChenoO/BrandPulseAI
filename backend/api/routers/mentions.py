# Phase 5: Mentions Router
# API endpoints for retrieving brand mentions from database

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, col, desc
from typing import Optional, List
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import MentionResponse, MentionList
from models.database import Mention, Brand, get_engine
from api.routers.auth import get_current_user
from models.database import User

router = APIRouter(
    prefix="/mentions",
    tags=["Mentions"]
)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
)


def get_db_session():
    """Dependency to get database session"""
    engine = get_engine(DATABASE_URL)
    with Session(engine) as session:
        yield session


# ============================================================================
# GET /mentions - List Mentions
# ============================================================================

@router.get("", response_model=MentionList)
def list_mentions(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive, neutral, negative)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of mentions to return"),
    offset: int = Query(0, ge=0, description="Number of mentions to skip"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter mentions from last N days"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    List mentions with optional filtering.

    **Filters:**
    - brand_id: Filter by specific brand
    - sentiment: Filter by sentiment (positive, neutral, negative)
    - source: Filter by source (google_news, hackernews, etc.)
    - days: Get mentions from last N days
    - limit: Max results (default: 50, max: 100)
    - offset: Pagination offset

    **Requires authentication.**
    """
    # Build query
    query = select(Mention)

    # Apply filters
    if brand_id is not None:
        query = query.where(Mention.brand_id == brand_id)

    if sentiment:
        # Case-insensitive sentiment filter
        sentiment_upper = sentiment.upper()
        query = query.where(col(Mention.sentiment_label).ilike(f"%{sentiment}%"))

    if source:
        # Case-insensitive source filter
        query = query.where(col(Mention.source).ilike(f"%{source}%"))

    if days:
        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Mention.processed_date >= cutoff_date)

    # Order by most recent first
    query = query.order_by(desc(Mention.processed_date))

    # Get total count (before pagination)
    count_query = select(Mention.id)
    if brand_id is not None:
        count_query = count_query.where(Mention.brand_id == brand_id)
    if sentiment:
        count_query = count_query.where(col(Mention.sentiment_label).ilike(f"%{sentiment}%"))
    if source:
        count_query = count_query.where(col(Mention.source).ilike(f"%{source}%"))
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count_query = count_query.where(Mention.processed_date >= cutoff_date)

    total = len(db.exec(count_query).all())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    mentions = db.exec(query).all()

    # Convert to response models
    mention_responses = [
        MentionResponse(
            id=m.id,
            brand_id=m.brand_id,
            source=m.source.value,
            title=m.title,
            url=m.url,
            content=m.content,
            sentiment_score=m.sentiment_score,
            sentiment_label=m.sentiment_label.value,
            published_date=m.published_date,
            ingested_date=m.ingested_date,
            processed_date=m.processed_date,
            author=m.author,
            points=m.points
        )
        for m in mentions
    ]

    return MentionList(
        mentions=mention_responses,
        total=total,
        limit=limit,
        offset=offset
    )


# ============================================================================
# GET /mentions/{mention_id} - Get Single Mention
# ============================================================================

@router.get("/{mention_id}", response_model=MentionResponse)
def get_mention(
    mention_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific mention by ID.

    **Requires authentication.**
    """
    mention = db.get(Mention, mention_id)

    if not mention:
        raise HTTPException(
            status_code=404,
            detail=f"Mention with ID {mention_id} not found"
        )

    return MentionResponse(
        id=mention.id,
        brand_id=mention.brand_id,
        source=mention.source.value,
        title=mention.title,
        url=mention.url,
        content=mention.content,
        sentiment_score=mention.sentiment_score,
        sentiment_label=mention.sentiment_label.value,
        published_date=mention.published_date,
        processed_date=mention.processed_date,
        author=mention.author,
        points=mention.points
    )


# ============================================================================
# GET /mentions/brand/{brand_id}/recent - Get Recent Mentions for Brand
# ============================================================================

@router.get("/brand/{brand_id}/recent", response_model=MentionList)
def get_recent_mentions_for_brand(
    brand_id: int,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of mentions"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get the most recent mentions for a specific brand.

    Useful for loading initial data on the dashboard.

    **Requires authentication.**
    """
    # Verify brand exists
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=404,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Get recent mentions
    query = select(Mention).where(
        Mention.brand_id == brand_id
    ).order_by(
        desc(Mention.processed_date)
    ).limit(limit)

    mentions = db.exec(query).all()

    # Get total count for this brand
    count_query = select(Mention.id).where(Mention.brand_id == brand_id)
    total = len(db.exec(count_query).all())

    # Convert to response
    mention_responses = [
        MentionResponse(
            id=m.id,
            brand_id=m.brand_id,
            source=m.source.value,
            title=m.title,
            url=m.url,
            content=m.content,
            sentiment_score=m.sentiment_score,
            sentiment_label=m.sentiment_label.value,
            published_date=m.published_date,
            processed_date=m.processed_date,
            author=m.author,
            points=m.points
        )
        for m in mentions
    ]

    return MentionList(
        mentions=mention_responses,
        total=total,
        limit=limit,
        offset=0
    )


# ============================================================================
# GET /mentions/stats/sentiment - Get Sentiment Statistics
# ============================================================================

@router.get("/stats/sentiment")
def get_sentiment_stats(
    brand_id: Optional[int] = Query(None, description="Filter by brand ID"),
    days: Optional[int] = Query(30, ge=1, le=365, description="Days to analyze"),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get sentiment statistics for mentions.

    Returns counts and percentages for positive, neutral, and negative sentiment.

    **Requires authentication.**
    """
    # Build base query
    query = select(Mention)

    if brand_id is not None:
        query = query.where(Mention.brand_id == brand_id)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(Mention.processed_date >= cutoff_date)

    # Get all mentions
    mentions = db.exec(query).all()

    # Calculate stats
    total = len(mentions)
    if total == 0:
        return {
            "total_mentions": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_percentage": 0.0,
            "neutral_percentage": 0.0,
            "negative_percentage": 0.0,
            "average_score": 0.0
        }

    positive_count = sum(1 for m in mentions if m.sentiment_label.value.lower() == "positive")
    neutral_count = sum(1 for m in mentions if m.sentiment_label.value.lower() == "neutral")
    negative_count = sum(1 for m in mentions if m.sentiment_label.value.lower() == "negative")

    average_score = sum(m.sentiment_score for m in mentions) / total

    return {
        "total_mentions": total,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "positive_percentage": (positive_count / total) * 100,
        "neutral_percentage": (neutral_count / total) * 100,
        "negative_percentage": (negative_count / total) * 100,
        "average_score": average_score,
        "period_days": days
    }
