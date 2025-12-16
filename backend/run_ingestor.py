# Phase 2: Unified Ingestor CLI
# Run multiple ingestors from a single command

import asyncio
import argparse
import sys
from ingestors.google_news import fetch_google_news_mentions, publish_to_redis as publish_news
from ingestors.hackernews import fetch_hackernews_mentions, publish_to_redis as publish_hn
from shared.redis_client import RedisStreamClient


async def run_all_ingestors(brand_name: str, limit: int, redis_url: str = None):
    """Run all ingestors for a brand"""
    print("\n" + "="*80)
    print("  BrandPulse - Phase 2: Multi-Source Ingestor")
    print("="*80)
    print(f"  Brand: {brand_name}")
    print(f"  Limit per source: {limit}")
    print("="*80 + "\n")

    # Initialize Redis
    try:
        redis_client = RedisStreamClient(redis_url=redis_url)
        print(f"✓ Connected to Redis at {redis_client.redis_url}\n")
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        print("  Make sure Redis is running (docker-compose up -d redis)")
        return 1

    total_published = 0

    # Fetch from Google News
    print("📰 Google News:")
    news_mentions = fetch_google_news_mentions(brand_name, limit)
    if news_mentions:
        print(f"   Publishing {len(news_mentions)} mentions...")
        count = publish_news(news_mentions, redis_client)
        total_published += count
        print(f"   ✓ Published {count} mentions")

    print()

    # Fetch from HackerNews
    print("🟠 HackerNews:")
    hn_mentions = await fetch_hackernews_mentions(brand_name, limit)
    if hn_mentions:
        print(f"   Publishing {len(hn_mentions)} mentions...")
        count = publish_hn(hn_mentions, redis_client)
        total_published += count
        print(f"   ✓ Published {count} mentions")

    print(f"\n{'='*80}")
    print(f"✅ Total mentions published: {total_published}")
    print(f"   Stream: {redis_client.STREAM_MENTIONS_RAW}")
    print(f"   Ready for processing by sentiment workers")
    print(f"{'='*80}\n")

    redis_client.close()
    return 0


async def main_async():
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 2: Run ingestors for brand monitoring"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Brand name to monitor (e.g., 'Tesla', 'OpenAI')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Mentions per source (default: 5)"
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["all", "news", "hackernews"],
        default="all",
        help="Which source to run (default: all)"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=None,
        help="Redis connection URL"
    )

    args = parser.parse_args()

    if args.source == "all":
        return await run_all_ingestors(args.brand, args.limit, args.redis_url)
    elif args.source == "news":
        # Run only Google News
        from ingestors.google_news import main as news_main
        sys.argv = [
            "google_news",
            "--brand", args.brand,
            "--limit", str(args.limit)
        ]
        if args.redis_url:
            sys.argv.extend(["--redis-url", args.redis_url])
        news_main()
    elif args.source == "hackernews":
        # Run only HackerNews
        from ingestors.hackernews import main as hn_main
        sys.argv = [
            "hackernews",
            "--brand", args.brand,
            "--limit", str(args.limit)
        ]
        if args.redis_url:
            sys.argv.extend(["--redis-url", args.redis_url])
        hn_main()

    return 0


def main():
    return asyncio.run(main_async())


if __name__ == "__main__":
    exit(main())
