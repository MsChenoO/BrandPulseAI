# Phase 3: Brands Router
# Handles brand CRUD operations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import BrandCreate, BrandResponse, MentionResponse, MentionList, SentimentTrendResponse, SentimentTrendPoint
from api.dependencies import get_db_session, NotFoundError
from models.database import Brand, Mention, User
from api.routers.auth import get_current_user
from datetime import datetime, timedelta
from sqlmodel import func
from sqlalchemy import case

router = APIRouter(
    prefix="/brands",
    tags=["Brands"]
)


# ============================================================================
# POST /brands - Create a new brand
# ============================================================================

@router.post(
    "",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new brand to monitor",
    description="""
    Creates a new brand for monitoring.

    The brand name must be unique for this user.

    **Requires authentication.**
    """
)
def create_brand(
    brand_data: BrandCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> BrandResponse:
    """
    Create a new brand for tracking.

    Args:
        brand_data: Brand creation data (name)
        db: Database session
        current_user: Authenticated user

    Returns:
        Created brand with ID and timestamp

    Raises:
        400: Brand already exists for this user
    """
    # Check if brand already exists for this user
    statement = select(Brand).where(
        Brand.name == brand_data.name,
        Brand.user_id == current_user.id
    )
    existing_brand = db.exec(statement).first()

    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand '{brand_data.name}' already exists"
        )

    # Create new brand for this user
    new_brand = Brand(
        name=brand_data.name,
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )

    # Save to database
    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)  # Get the auto-generated ID

    # Return response
    return BrandResponse(
        id=new_brand.id,
        name=new_brand.name,
        created_at=new_brand.created_at,
        mention_count=0  # New brand has no mentions yet
    )


# ============================================================================
# GET /brands - List all brands
# ============================================================================

@router.get(
    "",
    response_model=List[BrandResponse],
    summary="List all brands",
    description="""
    Returns all brands being monitored by the current user.

    **Requires authentication.**
    """
)
def list_brands(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[BrandResponse]:
    """
    List all brands for the current user.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of user's brands
    """
    statement = select(Brand).where(Brand.user_id == current_user.id)
    brands = db.exec(statement).all()

    # Convert to response models
    # Note: mention_count would require a join with Mention table
    # For now, we'll leave it as None
    return [
        BrandResponse(
            id=brand.id,
            name=brand.name,
            created_at=brand.created_at,
            mention_count=None  # TODO: Add count query
        )
        for brand in brands
    ]


# ============================================================================
# GET /brands/{brand_id} - Get single brand
# ============================================================================

@router.get(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Get a brand by ID",
    description="""
    Returns details of a specific brand owned by the current user.

    **Requires authentication.**
    """
)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> BrandResponse:
    """
    Get a brand by ID.

    Args:
        brand_id: Brand ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Brand details

    Raises:
        404: Brand not found or not owned by user
    """
    brand = db.get(Brand, brand_id)

    if not brand or brand.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    return BrandResponse(
        id=brand.id,
        name=brand.name,
        created_at=brand.created_at,
        mention_count=None  # TODO: Add count query
    )


# ============================================================================
# GET /brands/{brand_id}/mentions - Get mentions for a brand
# ============================================================================

@router.get(
    "/{brand_id}/mentions",
    response_model=MentionList,
    summary="Get mentions for a brand",
    description="""
    Returns all mentions for a specific brand with optional filtering.

    Filters:
    - source: Filter by source (google_news, hackernews)
    - sentiment: Filter by sentiment label
    - limit/offset: Pagination
    """
)
def get_brand_mentions(
    brand_id: int,
    db: Session = Depends(get_db_session),
    source: Optional[str] = Query(None, description="Filter by source"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment label"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> MentionList:
    """
    Get mentions for a brand with optional filters.

    Args:
        brand_id: Brand ID
        db: Database session
        source: Optional source filter
        sentiment: Optional sentiment filter
        limit: Maximum results
        offset: Pagination offset

    Returns:
        Paginated list of mentions

    Raises:
        404: Brand not found
    """
    # Check if brand exists
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Build query
    statement = select(Mention).where(Mention.brand_id == brand_id)

    # Apply filters
    if source:
        statement = statement.where(Mention.source == source)

    if sentiment:
        statement = statement.where(Mention.sentiment_label == sentiment)

    # Get total count (before pagination)
    count_statement = statement
    total = len(db.exec(count_statement).all())

    # Apply pagination
    statement = statement.offset(offset).limit(limit)

    # Execute query
    mentions = db.exec(statement).all()

    # Convert to response models
    mention_responses = [
        MentionResponse(
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
            highlights=None  # No highlights for database query
        )
        for mention in mentions
    ]

    # Calculate pagination info
    page = (offset // limit) + 1 if limit > 0 else 1

    return MentionList(
        mentions=mention_responses,
        total=total,
        page=page,
        page_size=limit
    )


# ============================================================================
# GET /brands/{brand_id}/sentiment-trend - Get sentiment trend over time
# ============================================================================

@router.get(
    "/{brand_id}/sentiment-trend",
    response_model=SentimentTrendResponse,
    summary="Get sentiment trend for a brand",
    description="""
    Returns aggregated sentiment data over time for visualization.

    Groups mentions by day and calculates average sentiment score,
    positive/neutral/negative counts, and total mentions per day.
    """
)
def get_sentiment_trend(
    brand_id: int,
    db: Session = Depends(get_db_session),
    days: int = Query(30, ge=1, le=365, description="Number of days to include")
) -> SentimentTrendResponse:
    """
    Get sentiment trend over time for a brand.

    Args:
        brand_id: Brand ID
        db: Database session
        days: Number of days to include (default 30)

    Returns:
        Time-series sentiment data

    Raises:
        404: Brand not found
    """
    # Check if brand exists
    brand = db.get(Brand, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query mentions with sentiment scores within date range
    statement = select(
        func.date(Mention.published_date).label("date"),
        func.avg(Mention.sentiment_score).label("avg_score"),
        func.count(Mention.id).label("mention_count"),
        func.sum(case((Mention.sentiment_label == "Positive", 1), else_=0)).label("positive_count"),
        func.sum(case((Mention.sentiment_label == "Neutral", 1), else_=0)).label("neutral_count"),
        func.sum(case((Mention.sentiment_label == "Negative", 1), else_=0)).label("negative_count")
    ).where(
        Mention.brand_id == brand_id,
        Mention.published_date >= start_date,
        Mention.published_date <= end_date,
        Mention.sentiment_score.isnot(None)  # Only include processed mentions
    ).group_by(
        func.date(Mention.published_date)
    ).order_by(
        func.date(Mention.published_date)
    )

    results = db.exec(statement).all()

    # Convert to response format
    trend_points = [
        SentimentTrendPoint(
            date=datetime.combine(row.date, datetime.min.time()) if row.date else datetime.utcnow(),
            average_score=float(row.avg_score or 0.0),
            mention_count=int(row.mention_count),
            positive_count=int(row.positive_count or 0),
            neutral_count=int(row.neutral_count or 0),
            negative_count=int(row.negative_count or 0)
        )
        for row in results
    ]

    # Calculate overall statistics
    total_mentions = sum(point.mention_count for point in trend_points)
    overall_avg = sum(point.average_score * point.mention_count for point in trend_points) / total_mentions if total_mentions > 0 else 0.0

    return SentimentTrendResponse(
        brand_id=brand_id,
        brand_name=brand.name,
        start_date=start_date,
        end_date=end_date,
        data_points=trend_points,
        overall_average=overall_avg
    )
