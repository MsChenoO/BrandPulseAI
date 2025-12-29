#!/usr/bin/env python3
"""
Test script to simulate real-time mention broadcasting via WebSocket.

This script demonstrates how to broadcast messages to connected WebSocket clients.
It imports the WebSocket service and sends test messages.

Usage:
    python tests/test_websocket_broadcast.py
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.websocket_service import broadcast_new_mention, broadcast_stats_update


async def test_broadcast_mentions():
    """
    Test broadcasting mention updates.

    Note: This requires the FastAPI server to be running and
    WebSocket clients to be connected to see the results.
    """
    print("🧪 Testing WebSocket Broadcasting")
    print("=" * 50)
    print()

    # Test mention data
    test_mentions = [
        {
            "id": 1001,
            "title": "Great product review on TechCrunch",
            "content": "This product has completely transformed our workflow. The integration is seamless and the performance is outstanding.",
            "url": "https://techcrunch.com/example-article-1",
            "source": "TechCrunch",
            "sentiment_label": "positive",
            "sentiment_score": 0.92,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 1002,
            "title": "Customer feedback on Hacker News",
            "content": "Been using this for a few weeks. It's decent, nothing spectacular but gets the job done.",
            "url": "https://news.ycombinator.com/example",
            "source": "Hacker News",
            "sentiment_label": "neutral",
            "sentiment_score": 0.55,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 1003,
            "title": "Negative review on Reddit",
            "content": "Unfortunately, the customer support has been terrible. Waiting for over a week for a response to my ticket.",
            "url": "https://reddit.com/r/example",
            "source": "Reddit",
            "sentiment_label": "negative",
            "sentiment_score": 0.25,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 1004,
            "title": "Product launch announcement",
            "content": "Excited to announce our new feature! This has been the most requested feature from our community.",
            "url": "https://example.com/blog/announcement",
            "source": "Company Blog",
            "sentiment_label": "positive",
            "sentiment_score": 0.88,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 1005,
            "title": "Breaking: Major security vulnerability found",
            "content": "Security researchers have discovered a critical vulnerability that could affect millions of users. Patch expected soon.",
            "url": "https://securitynews.com/breaking-vuln",
            "source": "Security News",
            "sentiment_label": "negative",
            "sentiment_score": 0.15,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        },
    ]

    print("📡 Broadcasting test mentions...")
    print()

    for i, mention in enumerate(test_mentions, 1):
        print(f"[{i}/5] Broadcasting mention: {mention['title'][:50]}...")
        print(f"       Sentiment: {mention['sentiment_label']} ({mention['sentiment_score']:.2f})")
        print(f"       Source: {mention['source']}")

        try:
            await broadcast_new_mention(mention, brand_id=mention['brand_id'])
            print(f"       ✅ Broadcast successful")
        except Exception as e:
            print(f"       ❌ Error: {e}")

        print()

        # Wait 2 seconds between broadcasts
        if i < len(test_mentions):
            print("       Waiting 2 seconds...")
            print()
            await asyncio.sleep(2)

    print()
    print("📊 Broadcasting stats update...")

    # Test stats update
    stats_data = {
        "total_mentions": 5,
        "positive_count": 2,
        "neutral_count": 1,
        "negative_count": 2,
        "new_today": 5,
    }

    try:
        await broadcast_stats_update(stats_data)
        print("✅ Stats broadcast successful")
        print(f"   Stats: {stats_data}")
    except Exception as e:
        print(f"❌ Stats broadcast error: {e}")

    print()
    print("=" * 50)
    print("✅ Test complete!")
    print()
    print("Note: These broadcasts only work if:")
    print("  1. The FastAPI server is running")
    print("  2. WebSocket clients are connected")
    print("  3. Clients are subscribed to brand ID 1")


async def continuous_broadcast():
    """
    Continuously broadcast mentions every 10 seconds for testing.
    """
    print("🔄 Starting continuous broadcast (Ctrl+C to stop)")
    print()

    counter = 1000

    while True:
        counter += 1

        mention = {
            "id": counter,
            "title": f"Test mention #{counter - 1000}",
            "content": f"This is a test mention broadcasted at {datetime.utcnow().isoformat()}",
            "url": "https://example.com/test",
            "source": "Test Source",
            "sentiment_label": ["positive", "neutral", "negative"][counter % 3],
            "sentiment_score": 0.5 + (counter % 50) / 100,
            "brand_id": 1,
            "published_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }

        print(f"Broadcasting mention #{counter - 1000}...")
        try:
            await broadcast_new_mention(mention, brand_id=1)
            print("✅ Sent")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("Waiting 10 seconds...")
        print()
        await asyncio.sleep(10)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test WebSocket broadcasting")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuously broadcast test mentions every 10 seconds",
    )
    args = parser.parse_args()

    if args.continuous:
        asyncio.run(continuous_broadcast())
    else:
        asyncio.run(test_broadcast_mentions())
