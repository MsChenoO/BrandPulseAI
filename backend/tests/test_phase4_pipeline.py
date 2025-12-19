#!/usr/bin/env python3
"""
Phase 4 Pipeline Test

Tests that mentions get embeddings and entities generated through the pipeline.
"""

import sys
import os
import time
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient
from models.database import get_engine, Brand, Mention
from sqlmodel import Session, select


def test_phase4_pipeline():
    """Test that Phase 4 features work end-to-end"""

    print("\n" + "="*80)
    print("PHASE 4 PIPELINE TEST")
    print("="*80)

    # Initialize clients
    redis_client = RedisStreamClient()
    database_url = "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
    engine = get_engine(database_url)

    # Create test mention
    test_mention = {
        "brand_name": "Tesla_Phase4_Test",
        "source": "google_news",
        "title": "Tesla announces breakthrough in battery technology with new lithium-ion cells",
        "url": f"https://test-phase4.com/article-{int(time.time())}",
        "content_snippet": "Tesla CEO Elon Musk unveiled a revolutionary battery technology at the company's headquarters in Palo Alto. The new lithium-ion cells promise 50% more range and faster charging times.",
        "published_date": datetime.utcnow().isoformat(),
        "author": "Tech Reporter"
    }

    print("\n1. Publishing test mention to Redis...")
    print(f"   Title: {test_mention['title'][:60]}...")
    message_id = redis_client.publish_raw_mention(test_mention)
    print(f"   ✓ Published with ID: {message_id}")

    print("\n2. Waiting for workers to process...")
    print("   ⚠ Make sure these workers are running:")
    print("     - Deduplication worker")
    print("     - Enrichment worker (optional)")
    print("     - Sentiment worker")
    print("\n   Waiting 15 seconds for processing...")
    time.sleep(15)

    print("\n3. Checking database for processed mention...")

    with Session(engine) as session:
        # Find the mention by URL
        mention = session.exec(
            select(Mention).where(Mention.url == test_mention['url'])
        ).first()

        if not mention:
            print("   ✗ FAIL: Mention not found in database")
            print("   Make sure the sentiment worker is running!")
            return False

        print(f"   ✓ Mention found in database (ID: {mention.id})")

        # Check sentiment analysis
        print(f"\n4. Verifying Phase 3 features (sentiment)...")
        if mention.sentiment_score is not None:
            print(f"   ✓ Sentiment: {mention.sentiment_label} ({mention.sentiment_score:+.2f})")
        else:
            print(f"   ✗ No sentiment score")

        # Check Phase 4: Embeddings
        print(f"\n5. Verifying Phase 4 features (embeddings)...")
        if mention.embedding is not None:
            embedding_dims = len(mention.embedding) if mention.embedding else 0
            if embedding_dims == 768:
                print(f"   ✓ Embedding: {embedding_dims} dimensions")
                print(f"   ✓ Sample values: [{mention.embedding[0]:.4f}, {mention.embedding[1]:.4f}, ..., {mention.embedding[-1]:.4f}]")
            else:
                print(f"   ✗ Embedding has wrong dimensions: {embedding_dims} (expected 768)")
        else:
            print(f"   ✗ No embedding generated")

        # Check Phase 4: Entity extraction
        print(f"\n6. Verifying Phase 4 features (entities)...")
        if mention.entities:
            print(f"   ✓ Entities extracted:")
            for entity_type, entity_list in mention.entities.items():
                if entity_list:
                    print(f"     - {entity_type.title()}: {', '.join(entity_list)}")

            # Expected entities in our test
            expected_entities = {
                'organizations': ['Tesla'],
                'people': ['Elon Musk'],
                'locations': ['Palo Alto']
            }

            all_good = True
            for entity_type, expected in expected_entities.items():
                found = mention.entities.get(entity_type, [])
                if not any(e in str(found) for e in expected):
                    print(f"   ⚠ Expected {entity_type} not all found: {expected}")
                    all_good = False

            if all_good:
                print(f"   ✓ All expected entities found!")
        else:
            print(f"   ✗ No entities extracted")

        # Summary
        print(f"\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        passed = []
        failed = []

        if mention.sentiment_score is not None:
            passed.append("Sentiment Analysis")
        else:
            failed.append("Sentiment Analysis")

        if mention.embedding and len(mention.embedding) == 768:
            passed.append("Embedding Generation (768-dim)")
        else:
            failed.append("Embedding Generation")

        if mention.entities and len(mention.entities) > 0:
            passed.append("Entity Extraction")
        else:
            failed.append("Entity Extraction")

        print(f"\n✓ PASSED ({len(passed)}/{len(passed) + len(failed)}):")
        for item in passed:
            print(f"  - {item}")

        if failed:
            print(f"\n✗ FAILED ({len(failed)}):")
            for item in failed:
                print(f"  - {item}")

        print("\n" + "="*80)

        # Cleanup
        print(f"\nCleaning up test data...")
        brand = session.get(Brand, mention.brand_id)
        session.delete(mention)
        if brand and brand.name == test_mention['brand_name']:
            session.delete(brand)
        session.commit()
        print(f"✓ Test data removed")

        return len(failed) == 0


if __name__ == "__main__":
    success = test_phase4_pipeline()
    exit(0 if success else 1)
