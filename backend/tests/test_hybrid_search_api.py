#!/usr/bin/env python3
"""
Test hybrid search API endpoint
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routers.search import hybrid_search
from api.schemas import HybridSearchRequest
from shared.elasticsearch_client import ElasticsearchClient

async def test_hybrid_search():
    """Test hybrid search endpoint directly"""

    # Test different semantic weights
    test_cases = [
        ("OpenAI", 0.5, "balanced"),
        ("artificial intelligence", 0.8, "semantic-heavy"),
        ("ChatGPT", 0.2, "keyword-heavy"),
    ]

    for query, weight, description in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {description}")
        print(f"Query: '{query}', Semantic Weight: {weight}")
        print(f"{'='*80}")

        request = HybridSearchRequest(
            query=query,
            limit=5,
            semantic_weight=weight,
            similarity_threshold=0.3
        )

        try:
            # Create mock Elasticsearch client
            es_mock = ElasticsearchClient()

            result = await hybrid_search(request, es=es_mock.es)

            print(f"\n✓ Success!")
            print(f"  Total results: {result.total}")
            print(f"  Time: {result.took_ms}ms")
            print(f"  Semantic weight: {result.semantic_weight}")

            for i, mention in enumerate(result.results, 1):
                print(f"\n  {i}. {mention.title[:60]}...")
                print(f"     Hybrid score: {mention.hybrid_score:.3f}")
                if mention.keyword_score:
                    print(f"     Keyword score: {mention.keyword_score:.3f}")
                if mention.semantic_score:
                    print(f"     Semantic score: {mention.semantic_score:.3f}")
                print(f"     Brand: {mention.brand_name}")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
