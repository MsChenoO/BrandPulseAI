# Phase 5: Testing Router
# Provides endpoints for testing real-time features (development only)

from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime
import random

from api.routers.auth import get_current_user
from models.database import User
from services.websocket_service import (
    broadcast_new_mention,
    broadcast_sentiment_update,
    broadcast_stats_update,
)

router = APIRouter(
    prefix="/test",
    tags=["Testing"]
)


@router.post("/broadcast/mention")
async def test_broadcast_mention(
    brand_id: Optional[int] = 1,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to broadcast a sample mention via WebSocket.

    Requires authentication. Only use in development.
    """
    # Generate random test mention
    sentiment_options = [
        ("positive", 0.85, "😊"),
        ("neutral", 0.55, "😐"),
        ("negative", 0.25, "😞"),
    ]
    sentiment, score, _ = random.choice(sentiment_options)

    sources = [
        "TechCrunch",
        "Hacker News",
        "Reddit",
        "Twitter",
        "Company Blog",
        "Google News",
    ]

    titles = [
        f"Great review of our product on {random.choice(sources)}",
        f"Customer feedback discussion on {random.choice(sources)}",
        f"New feature announcement on {random.choice(sources)}",
        f"Product comparison on {random.choice(sources)}",
        f"Industry news mentions us on {random.choice(sources)}",
    ]

    mention_data = {
        "id": random.randint(1000, 9999),
        "title": random.choice(titles),
        "content": f"This is a test mention broadcasted at {datetime.utcnow().isoformat()}. The sentiment is {sentiment}.",
        "url": f"https://example.com/test/{random.randint(100, 999)}",
        "source": random.choice(sources),
        "sentiment_label": sentiment,
        "sentiment_score": score,
        "brand_id": brand_id,
        "published_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat(),
    }

    # Broadcast via WebSocket
    await broadcast_new_mention(mention_data, brand_id=brand_id)

    return {
        "success": True,
        "message": "Test mention broadcasted",
        "data": mention_data,
    }


@router.post("/broadcast/stats")
async def test_broadcast_stats(
    brand_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to broadcast sample statistics via WebSocket.

    Requires authentication. Only use in development.
    """
    stats_data = {
        "total_mentions": random.randint(50, 200),
        "positive_count": random.randint(20, 100),
        "neutral_count": random.randint(10, 50),
        "negative_count": random.randint(5, 30),
        "new_today": random.randint(1, 20),
    }

    # Broadcast via WebSocket
    await broadcast_stats_update(stats_data, brand_id=brand_id)

    return {
        "success": True,
        "message": "Test stats broadcasted",
        "data": stats_data,
    }


@router.post("/broadcast/batch")
async def test_broadcast_batch(
    count: int = 5,
    delay_seconds: int = 2,
    brand_id: Optional[int] = 1,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to broadcast multiple mentions in sequence.

    Requires authentication. Only use in development.
    """
    import asyncio

    mentions = []

    for i in range(count):
        sentiment_options = [
            ("positive", 0.85, "😊"),
            ("neutral", 0.55, "😐"),
            ("negative", 0.25, "😞"),
        ]
        sentiment, score, _ = random.choice(sentiment_options)

        sources = ["TechCrunch", "Hacker News", "Reddit", "Twitter"]

        mention_data = {
            "id": random.randint(1000, 9999),
            "title": f"Test mention #{i + 1} - {random.choice(['Review', 'Discussion', 'Announcement'])}",
            "content": f"Batch test mention {i + 1} of {count}. Sentiment: {sentiment}.",
            "url": f"https://example.com/test/{random.randint(100, 999)}",
            "source": random.choice(sources),
            "sentiment_label": sentiment,
            "sentiment_score": score,
            "brand_id": brand_id,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }

        # Broadcast
        await broadcast_new_mention(mention_data, brand_id=brand_id)
        mentions.append(mention_data)

        # Wait between broadcasts
        if i < count - 1:
            await asyncio.sleep(delay_seconds)

    return {
        "success": True,
        "message": f"Broadcasted {count} test mentions",
        "count": len(mentions),
        "mentions": mentions,
    }
