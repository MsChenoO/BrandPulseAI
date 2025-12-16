# Phase 2: HackerNews Ingestor
# Fetches brand mentions from HackerNews Algolia API and publishes to Redis Streams

import httpx
import asyncio
from datetime import datetime
from typing import List, Dict
import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient


async def fetch_hackernews_mentions(brand_name: str, limit: int = 10) -> List[Dict]:
    """
    Fetch recent mentions of a brand from HackerNews using Algolia API.

    Args:
        brand_name: The brand to search for
        limit: Maximum number of stories to fetch

    Returns:
        List of mention dictionaries
    """
    try:
        # HackerNews Algolia Search API
        search_url = f"https://hn.algolia.com/api/v1/search?query={brand_name}&tags=story&hitsPerPage={limit}"

        print(f"🟠 Fetching HackerNews mentions for '{brand_name}'...")

        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        total_available = data.get('nbHits', 0)
        mentions = []

        for hit in data.get('hits', [])[:limit]:
            # Parse timestamp
            published_date = None
            if hit.get('created_at'):
                try:
                    published_date = datetime.fromisoformat(hit['created_at'].replace('Z', '+00:00'))
                except:
                    pass

            # Get URL (use story_url if available, otherwise HN item page)
            url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"

            mention = {
                "brand_name": brand_name,
                "source": "hackernews",
                "title": hit.get('title', ''),
                "url": url,
                "content_snippet": hit.get('story_text', '')[:500] if hit.get('story_text') else '',
                "published_date": published_date,
                "author": hit.get('author', 'unknown'),
                "points": hit.get('points', 0)
            }
            mentions.append(mention)

        print(f"✓ Found {total_available} stories, collected {len(mentions)} for processing")
        return mentions

    except Exception as e:
        print(f"✗ Error fetching HackerNews mentions: {e}")
        return []


def publish_to_redis(mentions: List[Dict], redis_client: RedisStreamClient) -> int:
    """
    Publish mentions to Redis Streams.

    Args:
        mentions: List of mention dictionaries
        redis_client: Redis client instance

    Returns:
        Number of messages published
    """
    published_count = 0

    for mention in mentions:
        try:
            message_id = redis_client.publish_raw_mention(mention)
            published_count += 1
            print(f"  → Published: {mention['title'][:60]}... (ID: {message_id})")
        except Exception as e:
            print(f"  ✗ Failed to publish mention: {e}")

    return published_count


async def main_async(args):
    """Async main function"""
    print("\n" + "="*80)
    print("  BrandPulse - Phase 2: HackerNews Ingestor")
    print("="*80)
    print(f"  Brand: {args.brand}")
    print(f"  Limit: {args.limit}")
    print("="*80 + "\n")

    # Initialize Redis client
    try:
        redis_client = RedisStreamClient(redis_url=args.redis_url)
        print(f"✓ Connected to Redis at {redis_client.redis_url}\n")
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        print("  Make sure Redis is running (docker-compose up -d redis)")
        return 1

    # Fetch mentions
    mentions = await fetch_hackernews_mentions(args.brand, args.limit)

    if not mentions:
        print("\n❌ No mentions found")
        redis_client.close()
        return 0

    # Publish to Redis
    print(f"\n📤 Publishing {len(mentions)} mentions to Redis Streams...")
    published_count = publish_to_redis(mentions, redis_client)

    print(f"\n✅ Successfully published {published_count}/{len(mentions)} mentions")
    print(f"   Stream: {redis_client.STREAM_MENTIONS_RAW}")
    print("\n" + "="*80 + "\n")

    redis_client.close()
    return 0


def main():
    """Main entry point for HackerNews ingestor"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 2: HackerNews Ingestor"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Brand name to monitor (e.g., 'Tesla', 'Python')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of stories to fetch (default: 10)"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=None,
        help="Redis connection URL (default: from env or localhost)"
    )

    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
