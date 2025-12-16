# Phase 2: Google News Ingestor
# Fetches brand mentions from Google News RSS and publishes to Redis Streams

import feedparser
from datetime import datetime
from typing import List, Dict
import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient


def fetch_google_news_mentions(brand_name: str, limit: int = 10) -> List[Dict]:
    """
    Fetch recent mentions of a brand from Google News RSS feed.

    Args:
        brand_name: The brand to search for
        limit: Maximum number of articles to fetch

    Returns:
        List of mention dictionaries
    """
    try:
        # Google News RSS search URL
        search_url = f"https://news.google.com/rss/search?q={brand_name}&hl=en-US&gl=US&ceid=US:en"

        print(f"📰 Fetching Google News mentions for '{brand_name}'...")
        feed = feedparser.parse(search_url)

        total_available = len(feed.entries)
        mentions = []

        for entry in feed.entries[:limit]:
            mention = {
                "brand_name": brand_name,
                "source": "google_news",
                "title": entry.title,
                "url": entry.link,
                "content_snippet": "",  # Will be fetched by worker
                "published_date": datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                "author": None,
                "points": None
            }
            mentions.append(mention)

        print(f"✓ Found {total_available} articles, collected {len(mentions)} for processing")
        return mentions

    except Exception as e:
        print(f"✗ Error fetching Google News: {e}")
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


def main():
    """Main entry point for Google News ingestor"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 2: Google News Ingestor"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Brand name to monitor (e.g., 'Tesla', 'Google')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of articles to fetch (default: 10)"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=None,
        help="Redis connection URL (default: from env or localhost)"
    )

    args = parser.parse_args()

    print("\n" + "="*80)
    print("  BrandPulse - Phase 2: Google News Ingestor")
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
    mentions = fetch_google_news_mentions(args.brand, args.limit)

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


if __name__ == "__main__":
    exit(main())
