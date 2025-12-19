# Temporary script to add test data to Elasticsearch
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.elasticsearch_client import ElasticsearchClient
from datetime import datetime

# Create client
client = ElasticsearchClient()

# Test mentions
test_mentions = [
    {
        "mention_id": 1001,
        "brand_id": 2,
        "brand_name": "Tesla",
        "title": "Tesla unveils new autonomous driving features",
        "content": "Tesla has announced groundbreaking improvements to their Full Self-Driving (FSD) system...",
        "url": "https://example.com/tesla-fsd",
        "source": "google_news",
        "author": "John Smith",
        "points": None,
        "sentiment_score": 0.8,
        "sentiment_label": "Positive",
        "published_date": datetime(2025, 12, 15),
        "ingested_date": datetime(2025, 12, 15, 10, 0),
        "processed_date": datetime(2025, 12, 15, 10, 5)
    },
    {
        "mention_id": 1002,
        "brand_id": 2,
        "brand_name": "Tesla",
        "title": "Tesla recalls vehicles due to software bug",
        "content": "Tesla is recalling certain vehicles to fix a software issue affecting the braking system...",
        "url": "https://example.com/tesla-recall",
        "source": "google_news",
        "author": "Jane Doe",
        "points": None,
        "sentiment_score": -0.6,
        "sentiment_label": "Negative",
        "published_date": datetime(2025, 12, 16),
        "ingested_date": datetime(2025, 12, 16, 9, 0),
        "processed_date": datetime(2025, 12, 16, 9, 5)
    },
    {
        "mention_id": 1003,
        "brand_id": 2,
        "brand_name": "Tesla",
        "title": "Tesla stock price remains stable",
        "content": "Tesla shares showed minimal movement today as investors await the company's quarterly results...",
        "url": "https://example.com/tesla-stock",
        "source": "hackernews",
        "author": "trader123",
        "points": 45,
        "sentiment_score": 0.0,
        "sentiment_label": "Neutral",
        "published_date": datetime(2025, 12, 17),
        "ingested_date": datetime(2025, 12, 17, 14, 0),
        "processed_date": datetime(2025, 12, 17, 14, 5)
    },
    {
        "mention_id": 1004,
        "brand_id": 1,
        "brand_name": "OpenAI",
        "title": "OpenAI releases GPT-5 with improved reasoning",
        "content": "OpenAI has launched GPT-5, featuring significantly enhanced reasoning capabilities and multimodal understanding...",
        "url": "https://example.com/openai-gpt5",
        "source": "hackernews",
        "author": "ai_enthusiast",
        "points": 324,
        "sentiment_score": 0.9,
        "sentiment_label": "Positive",
        "published_date": datetime(2025, 12, 18),
        "ingested_date": datetime(2025, 12, 18, 8, 0),
        "processed_date": datetime(2025, 12, 18, 8, 5)
    }
]

# Bulk index
count = client.bulk_index_mentions(test_mentions)
print(f"✓ Indexed {count} test mentions to Elasticsearch")

# Verify
import time
time.sleep(1)  # Wait for indexing

# Test search
results = client.search_mentions(query="autonomous driving", limit=5)
print(f"\n✓ Search for 'autonomous driving' returned {results['total']} results")

client.close()
