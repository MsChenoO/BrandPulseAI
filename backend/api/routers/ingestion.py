# Ingestion Router
# Handles triggering data ingestion for brands

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from typing import Optional
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.dependencies import get_db_session
from models.database import Brand, User
from api.routers.auth import get_current_user
from ingestors.google_news import fetch_google_news_mentions
from ingestors.hackernews import fetch_hackernews_mentions
from shared.redis_client import RedisStreamClient

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"]
)


async def ingest_brand_mentions(brand_id: int, brand_name: str, limit: int = 10):
    """
    Background task to ingest mentions for a brand.

    Args:
        brand_id: Brand ID to associate mentions with
        brand_name: Brand name to search for
        limit: Number of mentions per source
    """
    print(f"\n🔍 Starting ingestion for brand: {brand_name} (ID: {brand_id})")

    try:
        from datetime import datetime
        from models.database import get_engine

        # Initialize Redis
        redis_client = RedisStreamClient()

        # Fetch from Google News
        print(f"  📰 Fetching from Google News...")
        news_mentions = fetch_google_news_mentions(brand_name, limit)

        # Add brand_id to each mention
        for mention in news_mentions:
            mention['brand_id'] = brand_id
            mention['brand_name'] = brand_name

        # Publish to Redis
        if news_mentions:
            from ingestors.google_news import publish_to_redis as publish_news
            count = publish_news(news_mentions, redis_client)
            print(f"  ✓ Published {count} Google News mentions")

        # Fetch from HackerNews
        print(f"  🟠 Fetching from HackerNews...")
        hn_mentions = await fetch_hackernews_mentions(brand_name, limit)

        # Add brand_id to each mention
        for mention in hn_mentions:
            mention['brand_id'] = brand_id
            mention['brand_name'] = brand_name

        # Publish to Redis
        if hn_mentions:
            from ingestors.hackernews import publish_to_redis as publish_hn
            count = publish_hn(hn_mentions, redis_client)
            print(f"  ✓ Published {count} HackerNews mentions")

        redis_client.close()

        total = len(news_mentions) + len(hn_mentions)
        print(f"  ✅ Ingestion complete: {total} mentions published for {brand_name}")

        # Update brand's updated_at timestamp
        try:
            from models.database import Brand
            engine = get_engine()
            with Session(engine) as db:
                brand = db.get(Brand, brand_id)
                if brand:
                    brand.updated_at = datetime.utcnow()
                    db.add(brand)
                    db.commit()
        except Exception as update_error:
            print(f"  ⚠ Failed to update brand timestamp: {update_error}")

    except Exception as e:
        print(f"  ❌ Ingestion failed for {brand_name}: {e}")


@router.post(
    "/brands/{brand_id}/fetch",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger mention ingestion for a brand",
    description="""
    Triggers background ingestion of mentions from Google News and HackerNews.

    The mentions are published to Redis and will be processed by the sentiment worker.

    **Requires authentication and brand ownership.**
    """
)
async def trigger_brand_ingestion(
    brand_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Trigger ingestion for a specific brand.

    Args:
        brand_id: Brand ID to fetch mentions for
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Authenticated user
        limit: Number of mentions to fetch per source (default: 10)

    Returns:
        Status message

    Raises:
        404: Brand not found or not owned by user
    """
    # Verify brand exists and user owns it
    brand = db.get(Brand, brand_id)

    if not brand or brand.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Trigger ingestion in background
    background_tasks.add_task(
        ingest_brand_mentions,
        brand_id=brand.id,
        brand_name=brand.name,
        limit=limit
    )

    return {
        "message": f"Ingestion started for {brand.name}",
        "brand_id": brand_id,
        "status": "processing"
    }


@router.post(
    "/brands/{brand_id}/fetch-sync",
    status_code=status.HTTP_200_OK,
    summary="Fetch mentions synchronously (for testing)",
    description="""
    Synchronously fetches mentions - waits for completion before returning.

    Use /fetch endpoint instead for production (async background task).

    **Requires authentication and brand ownership.**
    """
)
async def fetch_brand_mentions_sync(
    brand_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """
    Synchronously fetch mentions for a brand (blocking).

    Args:
        brand_id: Brand ID to fetch mentions for
        db: Database session
        current_user: Authenticated user
        limit: Number of mentions to fetch per source (default: 10)

    Returns:
        Ingestion results

    Raises:
        404: Brand not found or not owned by user
    """
    # Verify brand exists and user owns it
    brand = db.get(Brand, brand_id)

    if not brand or brand.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found"
        )

    # Run ingestion synchronously
    await ingest_brand_mentions(
        brand_id=brand.id,
        brand_name=brand.name,
        limit=limit
    )

    return {
        "message": f"Ingestion complete for {brand.name}",
        "brand_id": brand_id,
        "status": "completed"
    }
