# Phase 3: Enrichment Worker
# Enriches mentions with metadata (domain, reading time, etc.)

import asyncio
import argparse
import os
import sys
from urllib.parse import urlparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient


class EnrichmentWorker:
    """Worker that enriches mentions with additional metadata"""

    def __init__(
        self,
        redis_url: str = None,
        consumer_name: str = "enrichment-worker-1"
    ):
        """
        Initialize the enrichment worker.

        Args:
            redis_url: Redis connection URL
            consumer_name: Unique name for this worker instance
        """
        # Redis client
        self.redis_client = RedisStreamClient(redis_url=redis_url)

        # Worker identity
        self.consumer_group = "enrichment-workers"
        self.consumer_name = consumer_name

        # Statistics
        self.stats = {
            "processed": 0,
            "enriched": 0,
            "errors": 0
        }

        print(f"✓ Enrichment Worker initialized")
        print(f"  - Redis: {self.redis_client.redis_url}")
        print(f"  - Consumer: {consumer_name}")

    def extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain name (e.g., 'example.com')
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            return "unknown"

    def calculate_reading_time(self, content: str) -> int:
        """
        Calculate estimated reading time in minutes.

        Assumes average reading speed of 200 words per minute.

        Args:
            content: Text content

        Returns:
            Reading time in minutes
        """
        if not content:
            return 0

        # Count words (simple split by whitespace)
        word_count = len(content.split())

        # Calculate reading time (200 words per minute)
        reading_time = max(1, round(word_count / 200))

        return reading_time

    def calculate_content_stats(self, content: str) -> dict:
        """
        Calculate content statistics.

        Args:
            content: Text content

        Returns:
            Dictionary with content statistics
        """
        if not content:
            return {
                "word_count": 0,
                "char_count": 0,
                "reading_time_minutes": 0
            }

        words = content.split()
        return {
            "word_count": len(words),
            "char_count": len(content),
            "reading_time_minutes": self.calculate_reading_time(content)
        }

    def enrich_mention(self, mention_data: dict) -> dict:
        """
        Enrich mention with additional metadata.

        Args:
            mention_data: Original mention data

        Returns:
            Enriched mention data
        """
        enriched = mention_data.copy()

        # Extract domain from URL
        enriched['domain'] = self.extract_domain(mention_data['url'])

        # Calculate content statistics
        content = mention_data.get('content_snippet', '') or mention_data.get('content', '')
        stats = self.calculate_content_stats(content)
        enriched['word_count'] = stats['word_count']
        enriched['char_count'] = stats['char_count']
        enriched['reading_time_minutes'] = stats['reading_time_minutes']

        # Add enrichment timestamp
        enriched['enriched_at'] = datetime.utcnow().isoformat()

        # Calculate content quality score (0-100)
        # Based on content length and presence of key fields
        quality_score = 0
        if content:
            quality_score += min(50, len(content) / 20)  # Up to 50 points for length
        if mention_data.get('title'):
            quality_score += 20
        if mention_data.get('author'):
            quality_score += 15
        if mention_data.get('published_date'):
            quality_score += 15

        enriched['quality_score'] = int(quality_score)

        return enriched

    async def process_mention(self, message_id: str, mention_data: dict):
        """
        Process a single mention: enrich with metadata.

        Args:
            message_id: Redis stream message ID
            mention_data: Mention data dictionary
        """
        self.stats["processed"] += 1

        try:
            # Enrich mention
            enriched_data = self.enrich_mention(mention_data)

            # Publish to processed stream (or could be a new enriched stream)
            # For now, we'll add it back to deduplicated stream with enrichments
            # In production, you might want a separate stream
            self.redis_client.publish_deduplicated_mention(enriched_data)

            self.stats["enriched"] += 1

            print(f"  ✓ Enriched: {mention_data['title'][:60]}...")
            print(f"    Domain: {enriched_data['domain']}")
            print(f"    Reading time: {enriched_data['reading_time_minutes']} min")
            print(f"    Quality score: {enriched_data['quality_score']}/100")

        except Exception as e:
            self.stats["errors"] += 1
            print(f"  ✗ Error enriching mention: {e}")
            raise  # Re-raise to prevent acknowledgment

        # Acknowledge message in Redis
        self.redis_client.acknowledge_deduplicated_message(self.consumer_group, message_id)

    async def run(self):
        """Main worker loop"""
        print(f"\n{'='*80}")
        print(f"  Enrichment Worker Running")
        print(f"  Consumer Group: {self.consumer_group}")
        print(f"  Consumer Name: {self.consumer_name}")
        print(f"  Input Stream: {self.redis_client.STREAM_MENTIONS_DEDUPLICATED}")
        print(f"  Output Stream: {self.redis_client.STREAM_MENTIONS_DEDUPLICATED} (enriched)")
        print(f"{'='*80}\n")

        try:
            for message_id, mention_data in self.redis_client.consume_deduplicated_mentions(
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
        """Print enrichment statistics"""
        total = self.stats["processed"]
        enriched = self.stats["enriched"]
        errors = self.stats["errors"]

        success_rate = (enriched / total * 100) if total > 0 else 0

        print(f"\n  📊 Statistics:")
        print(f"    Processed: {total}")
        print(f"    Enriched: {enriched}")
        print(f"    Errors: {errors}")
        print(f"    Success rate: {success_rate:.1f}%")
        print()

    def close(self):
        """Cleanup resources"""
        self.redis_client.close()


async def main_async(args):
    """Async main function"""
    worker = EnrichmentWorker(
        redis_url=args.redis_url,
        consumer_name=args.consumer_name
    )

    await worker.run()
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 3: Enrichment Worker"
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
        default="enrichment-worker-1",
        help="Unique consumer name (default: enrichment-worker-1)"
    )

    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
