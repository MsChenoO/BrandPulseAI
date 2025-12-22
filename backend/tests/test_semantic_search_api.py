#!/usr/bin/env python3
"""
Test semantic search API endpoint
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routers.search import semantic_search
from api.schemas import SemanticSearchRequest

async def test_semantic_search():
    """Test semantic search endpoint directly"""

    request = SemanticSearchRequest(
        query="artificial intelligence and machine learning",
        limit=5,
        similarity_threshold=0.3
    )

    print(f"Testing semantic search with query: {request.query}")

    try:
        result = await semantic_search(request)
        print(f"\n✓ Success!")
        print(f"  Total results: {result.total}")
        print(f"  Time: {result.took_ms}ms")

        for mention in result.results:
            print(f"\n  - {mention.title[:60]}...")
            print(f"    Similarity: {mention.similarity_score:.3f}")
            print(f"    Brand: {mention.brand_name}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_semantic_search())
