# Phase 3: Brands Router
# Handles brand CRUD operations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.schemas import BrandCreate, BrandResponse, MentionResponse, MentionList
from api.dependencies import get_db_session, NotFoundError
from models.database import Brand, Mention
from datetime import datetime

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

    The brand name must be unique. If the brand already exists, returns 400 error.
    """
)
def create_brand(
    brand_data: BrandCreate,
    db: Session = Depends(get_db_session)
) -> BrandResponse:
    """
    Create a new brand for tracking.

    Args:
        brand_data: Brand creation data (name)
        db: Database session

    Returns:
        Created brand with ID and timestamp

    Raises:
        400: Brand already exists
    """
    # Check if brand already exists
    statement = select(Brand).where(Brand.name == brand_data.name)
    existing_brand = db.exec(statement).first()

    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand '{brand_data.name}' already exists"
        )

    # Create new brand
    new_brand = Brand(
        name=brand_data.name,
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
    description="Returns all brands being monitored, with optional mention counts."
)
def list_brands(
    db: Session = Depends(get_db_session)
) -> List[BrandResponse]:
    """
    List all brands.

    Args:
        db: Database session

    Returns:
        List of all brands
    """
    statement = select(Brand)
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
    description="Returns details of a specific brand."
)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db_session)
) -> BrandResponse:
    """
    Get a brand by ID.

    Args:
        brand_id: Brand ID
        db: Database session

    Returns:
        Brand details

    Raises:
        404: Brand not found
    """
    brand = db.get(Brand, brand_id)

    if not brand:
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
