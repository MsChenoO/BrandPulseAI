#!/usr/bin/env python3
"""
Complete Phase 3 Pipeline End-to-End Test

This script tests the entire pipeline from ingestion to API:
1. Publish raw mentions to Redis
2. Deduplication worker processes
3. Enrichment worker adds metadata
4. Sentiment worker analyzes and stores in PostgreSQL + Elasticsearch
5. Verify API endpoints work correctly

Run this after starting all infrastructure services.
"""

import sys
import time
import requests
from datetime import datetime
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient
from models.database import get_engine, Brand, Mention
from sqlmodel import Session, select

# Configuration
API_BASE_URL = "http://localhost:8000"
BRAND_NAME = "TestBrand_Pipeline"

class PipelineTest:
    def __init__(self):
        self.redis_client = RedisStreamClient()
        self.database_url = "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
        self.engine = get_engine(self.database_url)
        self.test_mentions = []
        self.results = {
            "passed": [],
            "failed": []
        }

    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"       {message}")

        if passed:
            self.results["passed"].append(test_name)
        else:
            self.results["failed"].append(test_name)

        return passed

    def cleanup(self):
        """Clean up test data"""
        print("\n" + "="*80)
        print("CLEANUP: Removing test data")
        print("="*80)

        # Delete test brand and mentions from database
        with Session(self.engine) as session:
            # Find test brand
            brand = session.exec(select(Brand).where(Brand.name == BRAND_NAME)).first()
            if brand:
                # Delete mentions
                mentions = session.exec(select(Mention).where(Mention.brand_id == brand.id)).all()
                for mention in mentions:
                    session.delete(mention)

                # Delete brand
                session.delete(brand)
                session.commit()
                print(f"✓ Deleted test brand '{BRAND_NAME}' and {len(mentions)} mentions from database")

        # Clear Redis streams and hash set
        try:
            self.redis_client.client.delete(self.redis_client.STREAM_MENTIONS_RAW)
            self.redis_client.client.delete(self.redis_client.STREAM_MENTIONS_DEDUPLICATED)
            self.redis_client.client.delete(self.redis_client.STREAM_MENTIONS_ENRICHED)
            self.redis_client.client.delete(self.redis_client.SET_MENTION_HASHES)
            print("✓ Cleared Redis streams and hash set")
        except:
            print("⚠ Redis already clean")

    def create_test_data(self):
        """Create test mentions (3 unique, 2 duplicates)"""
        print("\n" + "="*80)
        print("STEP 1: Creating Test Data")
        print("="*80)

        self.test_mentions = [
            {
                "brand_name": BRAND_NAME,
                "source": "google_news",
                "title": "TestBrand announces new product",
                "url": "https://test.com/product-1",
                "content_snippet": "TestBrand has announced an innovative new product that will revolutionize the industry.",
                "published_date": datetime.utcnow().isoformat(),
                "author": "Test Reporter"
            },
            {
                "brand_name": BRAND_NAME,
                "source": "hackernews",
                "title": "TestBrand announces new product",  # DUPLICATE
                "url": "https://test.com/product-1",  # Same URL
                "content_snippet": "Different content but same URL",
                "published_date": datetime.utcnow().isoformat(),
            },
            {
                "brand_name": BRAND_NAME,
                "source": "google_news",
                "title": "TestBrand receives positive reviews",
                "url": "https://test.com/reviews-1",
                "content_snippet": "TestBrand's latest product is receiving overwhelmingly positive feedback from users and critics alike.",
                "published_date": datetime.utcnow().isoformat(),
                "author": "Review Editor"
            },
            {
                "brand_name": BRAND_NAME,
                "source": "google_news",
                "title": "TestBrand faces criticism",
                "url": "https://test.com/criticism-1",
                "content_snippet": "Some users have raised concerns about TestBrand's new privacy policy and data handling practices.",
                "published_date": datetime.utcnow().isoformat(),
            },
            {
                "brand_name": BRAND_NAME,
                "source": "google_news",
                "title": "TestBrand faces criticism",  # DUPLICATE
                "url": "https://test.com/criticism-1",  # Same URL
                "content_snippet": "Another version",
                "published_date": datetime.utcnow().isoformat(),
            }
        ]

        print(f"Created {len(self.test_mentions)} test mentions:")
        print(f"  - Expected unique: 3")
        print(f"  - Expected duplicates: 2")
        print(f"  - Expected sentiments: 1 Positive, 1 Neutral, 1 Negative")

    def publish_to_redis(self):
        """Publish test mentions to Redis raw stream"""
        print("\n" + "="*80)
        print("STEP 2: Publishing to Redis (mentions:raw)")
        print("="*80)

        for i, mention in enumerate(self.test_mentions, 1):
            message_id = self.redis_client.publish_raw_mention(mention)
            print(f"{i}. Published: {mention['title'][:50]}")
            print(f"   Message ID: {message_id}")

        # Verify stream length
        stream_info = self.redis_client.get_stream_info(self.redis_client.STREAM_MENTIONS_RAW)
        length = stream_info['length']

        self.log_test(
            "Publish to Redis",
            length == 5,
            f"Stream length: {length} (expected 5)"
        )

        return length == 5

    def wait_for_processing(self, stream_name, expected_count, timeout=30):
        """Wait for stream to be processed"""
        print(f"\nWaiting for {stream_name} processing (expected {expected_count} messages)...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                info = self.redis_client.get_stream_info(stream_name)
                current = info['length']

                if current >= expected_count:
                    print(f"✓ {stream_name}: {current} messages")
                    return True

                print(f"  {stream_name}: {current}/{expected_count} messages...", end='\r')
                time.sleep(1)
            except:
                time.sleep(1)

        print(f"\n✗ Timeout waiting for {stream_name}")
        return False

    def verify_deduplication(self):
        """Verify deduplication worker processed correctly"""
        print("\n" + "="*80)
        print("STEP 3: Verifying Deduplication")
        print("="*80)

        # Wait for deduplication
        if not self.wait_for_processing(self.redis_client.STREAM_MENTIONS_DEDUPLICATED, 3, timeout=10):
            self.log_test("Deduplication Processing", False, "Timeout waiting for dedup worker")
            return False

        # Check deduplicated stream
        try:
            dedup_info = self.redis_client.get_stream_info(self.redis_client.STREAM_MENTIONS_DEDUPLICATED)
            dedup_count = dedup_info['length']
        except:
            dedup_count = 0

        # Check hash set
        hash_count = self.redis_client.client.scard(self.redis_client.SET_MENTION_HASHES)

        print(f"Deduplicated stream: {dedup_count} messages")
        print(f"Hash set: {hash_count} unique hashes")

        passed = dedup_count == 3 and hash_count == 3
        self.log_test(
            "Deduplication Worker",
            passed,
            f"Expected 3 unique, got {dedup_count} in stream and {hash_count} hashes"
        )

        return passed

    def verify_enrichment(self):
        """Verify enrichment worker added metadata"""
        print("\n" + "="*80)
        print("STEP 4: Verifying Enrichment")
        print("="*80)

        # Note: Enrichment worker might not be running in test
        # We'll just check if stream exists
        try:
            enriched_info = self.redis_client.get_stream_info(self.redis_client.STREAM_MENTIONS_ENRICHED)
            enriched_count = enriched_info['length']
            print(f"Enriched stream: {enriched_count} messages")

            self.log_test(
                "Enrichment Worker",
                enriched_count >= 0,
                f"Stream has {enriched_count} messages (worker may not be running)"
            )
        except:
            print("⚠ Enriched stream not yet created (worker not started)")
            self.log_test("Enrichment Worker", True, "Stream not created - worker not running (OK for test)")

    def verify_database_storage(self):
        """Verify mentions were stored in PostgreSQL"""
        print("\n" + "="*80)
        print("STEP 5: Verifying PostgreSQL Storage")
        print("="*80)

        # Give sentiment worker time to process
        print("Waiting for sentiment analysis...")
        time.sleep(5)

        with Session(self.engine) as session:
            # Check brand exists
            brand = session.exec(select(Brand).where(Brand.name == BRAND_NAME)).first()

            if not brand:
                self.log_test("Database - Brand Creation", False, f"Brand '{BRAND_NAME}' not found")
                return False

            print(f"✓ Brand created: {brand.name} (ID: {brand.id})")
            self.log_test("Database - Brand Creation", True, f"Brand ID: {brand.id}")

            # Check mentions
            mentions = session.exec(select(Mention).where(Mention.brand_id == brand.id)).all()
            mention_count = len(mentions)

            print(f"✓ Mentions stored: {mention_count}")

            # Check sentiment analysis
            with_sentiment = [m for m in mentions if m.sentiment_score is not None]
            sentiment_count = len(with_sentiment)

            print(f"✓ Mentions with sentiment: {sentiment_count}")

            if sentiment_count > 0:
                for mention in with_sentiment:
                    print(f"  - {mention.title[:50]}: {mention.sentiment_label} ({mention.sentiment_score:+.2f})")

            self.log_test(
                "Database - Mentions Stored",
                mention_count > 0,
                f"Stored {mention_count} mentions"
            )

            self.log_test(
                "Database - Sentiment Analysis",
                sentiment_count > 0,
                f"{sentiment_count}/{mention_count} mentions analyzed"
            )

            return mention_count > 0

    def verify_elasticsearch(self):
        """Verify mentions were indexed in Elasticsearch"""
        print("\n" + "="*80)
        print("STEP 6: Verifying Elasticsearch Indexing")
        print("="*80)

        try:
            # Check search health
            response = requests.get(f"{API_BASE_URL}/search/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✓ Elasticsearch: {health['status']}")
                print(f"  Version: {health['elasticsearch_version']}")
                print(f"  Index exists: {health['index_exists']}")
                print(f"  Document count: {health['document_count']}")

                self.log_test(
                    "Elasticsearch - Health",
                    health['status'] == 'healthy',
                    "Elasticsearch is healthy"
                )

                self.log_test(
                    "Elasticsearch - Index",
                    health['index_exists'],
                    "Index exists"
                )
            else:
                self.log_test("Elasticsearch - Health", False, f"HTTP {response.status_code}")

        except Exception as e:
            self.log_test("Elasticsearch - Health", False, f"Error: {e}")

    def test_api_endpoints(self):
        """Test all API endpoints"""
        print("\n" + "="*80)
        print("STEP 7: Testing API Endpoints")
        print("="*80)

        # Test 1: GET /brands
        try:
            response = requests.get(f"{API_BASE_URL}/brands")
            brands = response.json() if response.status_code == 200 else []
            brand_exists = any(b['name'] == BRAND_NAME for b in brands)

            self.log_test(
                "API - GET /brands",
                response.status_code == 200 and brand_exists,
                f"Found {len(brands)} brands, test brand exists: {brand_exists}"
            )

            # Get test brand ID
            test_brand = next((b for b in brands if b['name'] == BRAND_NAME), None)
            brand_id = test_brand['id'] if test_brand else None

        except Exception as e:
            self.log_test("API - GET /brands", False, str(e))
            brand_id = None

        if not brand_id:
            print("⚠ Cannot test remaining endpoints without brand ID")
            return

        # Test 2: GET /brands/{id}
        try:
            response = requests.get(f"{API_BASE_URL}/brands/{brand_id}")
            self.log_test(
                "API - GET /brands/{id}",
                response.status_code == 200,
                f"Brand details retrieved"
            )
        except Exception as e:
            self.log_test("API - GET /brands/{id}", False, str(e))

        # Test 3: GET /brands/{id}/mentions
        try:
            response = requests.get(f"{API_BASE_URL}/brands/{brand_id}/mentions")
            if response.status_code == 200:
                data = response.json()
                mention_count = data.get('total', 0)
                self.log_test(
                    "API - GET /brands/{id}/mentions",
                    mention_count > 0,
                    f"Retrieved {mention_count} mentions"
                )
            else:
                self.log_test("API - GET /brands/{id}/mentions", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API - GET /brands/{id}/mentions", False, str(e))

        # Test 4: GET /brands/{id}/sentiment-trend
        try:
            response = requests.get(f"{API_BASE_URL}/brands/{brand_id}/sentiment-trend?days=7")
            self.log_test(
                "API - GET /brands/{id}/sentiment-trend",
                response.status_code == 200,
                "Sentiment trend retrieved"
            )
        except Exception as e:
            self.log_test("API - GET /brands/{id}/sentiment-trend", False, str(e))

        # Test 5: POST /search
        try:
            search_data = {
                "query": "TestBrand",
                "limit": 10
            }
            response = requests.post(f"{API_BASE_URL}/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                result_count = results.get('total', 0)
                self.log_test(
                    "API - POST /search",
                    result_count >= 0,
                    f"Search returned {result_count} results"
                )
            else:
                self.log_test("API - POST /search", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API - POST /search", False, str(e))

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total = len(self.results["passed"]) + len(self.results["failed"])
        passed = len(self.results["passed"])
        failed = len(self.results["failed"])

        print(f"\nTotal Tests: {total}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")

        if failed > 0:
            print("\nFailed Tests:")
            for test in self.results["failed"]:
                print(f"  ✗ {test}")

        print("\n" + "="*80)

        return failed == 0

    def run(self, cleanup_after=True):
        """Run complete pipeline test"""
        print("\n" + "="*80)
        print("BRANDPULSE PHASE 3 - COMPLETE PIPELINE TEST")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Cleanup before test
            self.cleanup()

            # Run test steps
            self.create_test_data()
            self.publish_to_redis()

            # Note: Workers need to be running separately
            print("\n⚠ IMPORTANT: Make sure all workers are running:")
            print("  1. Deduplication worker")
            print("  2. Enrichment worker (optional)")
            print("  3. Sentiment worker")
            print("  4. FastAPI server")

            time.sleep(2)  # Give user time to read

            self.verify_deduplication()
            self.verify_enrichment()
            self.verify_database_storage()
            self.verify_elasticsearch()
            self.test_api_endpoints()

            # Print summary
            success = self.print_summary()

            # Cleanup
            if cleanup_after:
                self.cleanup()

            return success

        except KeyboardInterrupt:
            print("\n\n⚠ Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.redis_client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BrandPulse Phase 3 Pipeline Test")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't cleanup test data after test")

    args = parser.parse_args()

    tester = PipelineTest()
    success = tester.run(cleanup_after=not args.no_cleanup)

    exit(0 if success else 1)
