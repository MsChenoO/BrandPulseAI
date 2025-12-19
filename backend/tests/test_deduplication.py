#!/usr/bin/env python3
# Test script for deduplication worker

import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient
from datetime import datetime

# Create Redis client
redis_client = RedisStreamClient()

print("Testing Deduplication Worker")
print("="*80)

# Test mentions - some are duplicates
test_mentions = [
    {
        "brand_name": "Tesla",
        "source": "google_news",
        "title": "Tesla announces new Model 3",
        "url": "https://example.com/tesla-model-3",
        "content_snippet": "Tesla has announced a new Model 3 variant...",
        "published_date": datetime.utcnow().isoformat()
    },
    {
        "brand_name": "Tesla",
        "source": "hackernews",
        "title": "Tesla announces new Model 3",  # Same title
        "url": "https://example.com/tesla-model-3",  # Same URL - DUPLICATE
        "content_snippet": "Different snippet but same URL",
        "published_date": datetime.utcnow().isoformat()
    },
    {
        "brand_name": "Apple",
        "source": "google_news",
        "title": "Apple releases iPhone 16",
        "url": "https://example.com/iphone-16",
        "content_snippet": "Apple has released the new iPhone 16...",
        "published_date": datetime.utcnow().isoformat()
    },
    {
        "brand_name": "Tesla",
        "source": "google_news",
        "title": "Tesla stock rises",
        "url": "https://example.com/tesla-stock",
        "content_snippet": "Tesla stock price increased...",
        "published_date": datetime.utcnow().isoformat()
    },
    {
        "brand_name": "Tesla",
        "source": "google_news",
        "title": "Tesla announces new Model 3",  # Same title
        "url": "https://example.com/tesla-model-3",  # Same URL - DUPLICATE AGAIN
        "content_snippet": "Yet another version",
        "published_date": datetime.utcnow().isoformat()
    },
]

print("\nPublishing test mentions to mentions:raw stream...")
print(f"Total mentions: {len(test_mentions)}")
print(f"Expected unique: 3 (Tesla Model 3, iPhone 16, Tesla stock)")
print(f"Expected duplicates: 2\n")

for i, mention in enumerate(test_mentions, 1):
    message_id = redis_client.publish_raw_mention(mention)
    print(f"{i}. Published: {mention['title'][:50]}")
    print(f"   URL: {mention['url']}")
    print(f"   Message ID: {message_id}")

print("\n" + "="*80)
print("✓ Test mentions published successfully!")
print("\nNow run the deduplication worker:")
print("  python workers/deduplication_worker.py")
print("\nThen check the deduplicated stream:")
print("  redis-cli XLEN mentions:deduplicated")
print("  (Should be 3)")
print("\nAnd check the duplicates count from worker output")
print("="*80)

redis_client.close()
