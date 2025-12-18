# Phase 3: Deduplication Worker
# Consumes raw mentions from Redis Streams, deduplicates, and publishes unique mentions

import asyncio
import hashlib
import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient


class DeduplicationWorker:
    """Worker that deduplicates mentions based on URL + title hash"""

    def __init__(
        self,
        redis_url: str = None,
        consumer_name: str = "dedup-worker-1"
    ):
        """
        Initialize the deduplication worker.

        Args:
            redis_url: Redis connection URL
            consumer_name: Unique name for this worker instance
        """
        # Redis client
        self.redis_client = RedisStreamClient(redis_url=redis_url)

        # Worker identity
        self.consumer_group = "deduplication-workers"
        self.consumer_name = consumer_name

        # Statistics
        self.stats = {
            "processed": 0,
            "unique": 0,
            "duplicates": 0
        }

        print(f"✓ Deduplication Worker initialized")
        print(f"  - Redis: {self.redis_client.redis_url}")
        print(f"  - Consumer: {consumer_name}")

    def calculate_mention_hash(self, url: str, title: str) -> str:
        """
        Calculate a unique hash for a mention based on URL and title.

        Args:
            url: Mention URL
            title: Mention title

        Returns:
            SHA256 hash string
        """
        # Normalize inputs
        normalized_url = url.lower().strip()
        normalized_title = title.lower().strip()

        # Create hash from URL + title
        content = f"{normalized_url}|{normalized_title}"
        hash_object = hashlib.sha256(content.encode('utf-8'))
        return hash_object.hexdigest()

    async def process_mention(self, message_id: str, mention_data: dict):
        """
        Process a single mention: check for duplicates, publish if unique.

        Args:
            message_id: Redis stream message ID
            mention_data: Mention data dictionary
        """
        self.stats["processed"] += 1

        # Calculate hash
        mention_hash = self.calculate_mention_hash(
            mention_data['url'],
            mention_data['title']
        )

        # Check if duplicate
        is_duplicate = self.redis_client.check_mention_hash(mention_hash)

        if is_duplicate:
            self.stats["duplicates"] += 1
            print(f"  ⚠ Duplicate: {mention_data['title'][:60]}...")
            print(f"    Hash: {mention_hash[:16]}...")
        else:
            # New mention - add hash to set
            self.redis_client.add_mention_hash(mention_hash)
            self.stats["unique"] += 1

            # Add hash to mention data for tracking
            mention_data['content_hash'] = mention_hash

            # Publish to deduplicated stream
            self.redis_client.publish_deduplicated_mention(mention_data)

            print(f"  ✓ Unique: {mention_data['title'][:60]}...")
            print(f"    Hash: {mention_hash[:16]}...")

        # Acknowledge message in Redis
        self.redis_client.acknowledge_message(self.consumer_group, message_id)

    async def run(self):
        """Main worker loop"""
        print(f"\n{'='*80}")
        print(f"  Deduplication Worker Running")
        print(f"  Consumer Group: {self.consumer_group}")
        print(f"  Consumer Name: {self.consumer_name}")
        print(f"  Input Stream: {self.redis_client.STREAM_MENTIONS_RAW}")
        print(f"  Output Stream: {self.redis_client.STREAM_MENTIONS_DEDUPLICATED}")
        print(f"{'='*80}\n")

        try:
            for message_id, mention_data in self.redis_client.consume_raw_mentions(
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
                block_ms=5000,
                count=1
            ):
                try:
                    await self.process_mention(message_id, mention_data)

                    # Print stats every 10 mentions
                    if self.stats["processed"] % 10 == 0:
                        self.print_stats()

                except Exception as e:
                    print(f"  ✗ Error processing mention: {e}")
                    # Don't acknowledge - message will be retried

        except KeyboardInterrupt:
            print("\n\n✓ Worker stopped by user")
            self.print_stats()
        except Exception as e:
            print(f"\n✗ Worker error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.redis_client.close()

    def print_stats(self):
        """Print deduplication statistics"""
        total = self.stats["processed"]
        unique = self.stats["unique"]
        duplicates = self.stats["duplicates"]

        duplicate_rate = (duplicates / total * 100) if total > 0 else 0

        print(f"\n  📊 Statistics:")
        print(f"    Processed: {total}")
        print(f"    Unique: {unique}")
        print(f"    Duplicates: {duplicates} ({duplicate_rate:.1f}%)")
        print()

    def close(self):
        """Cleanup resources"""
        self.redis_client.close()


async def main_async(args):
    """Async main function"""
    worker = DeduplicationWorker(
        redis_url=args.redis_url,
        consumer_name=args.consumer_name
    )

    await worker.run()
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 3: Deduplication Worker"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=None,
        help="Redis connection URL"
    )
    parser.add_argument(
        "--consumer-name",
        type=str,
        default="dedup-worker-1",
        help="Unique consumer name (default: dedup-worker-1)"
    )

    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
