# Phase 2/3/4: Sentiment Analysis Worker
# Consumes enriched mentions from Redis Streams, analyzes sentiment, generates embeddings,
# extracts entities, persists to PostgreSQL, and indexes to Elasticsearch

import asyncio
import httpx
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from datetime import datetime
import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient
from shared.elasticsearch_client import ElasticsearchClient, MENTIONS_INDEX
from shared.embedding_service import EmbeddingService
from shared.entity_extraction_service import EntityExtractionService
from models.database import (
    get_engine, create_db_and_tables, get_session,
    Brand, Mention, SentimentLabel, Source
)


class SentimentWorker:
    """Worker that processes mentions: fetch content, analyze sentiment, save to DB"""

    def __init__(
        self,
        redis_url: str = None,
        database_url: str = None,
        elasticsearch_url: str = None,
        ollama_model: str = "llama3",
        consumer_name: str = "sentiment-worker-1"
    ):
        """
        Initialize the sentiment worker.

        Args:
            redis_url: Redis connection URL
            database_url: PostgreSQL connection URL
            elasticsearch_url: Elasticsearch connection URL
            ollama_model: Ollama model name for sentiment analysis
            consumer_name: Unique name for this worker instance
        """
        # Redis client
        self.redis_client = RedisStreamClient(redis_url=redis_url)

        # Database setup
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
            )
        self.engine = get_engine(database_url)
        create_db_and_tables(self.engine)

        # Elasticsearch setup
        self.es_client = ElasticsearchClient(es_url=elasticsearch_url)
        # Ensure index exists
        self.es_client.create_index(MENTIONS_INDEX)

        # LLM for sentiment analysis
        self.llm = ChatOllama(model=ollama_model)
        self.ollama_model = ollama_model

        # Phase 4: Embedding service for semantic search
        self.embedding_service = EmbeddingService()

        # Phase 4: Entity extraction service
        self.entity_service = EntityExtractionService(model=ollama_model)

        # Worker identity
        self.consumer_group = "sentiment-workers"
        self.consumer_name = consumer_name

        print(f"✓ Sentiment Worker initialized (Phase 4)")
        print(f"  - Redis: {self.redis_client.redis_url}")
        print(f"  - Database: {database_url}")
        print(f"  - Elasticsearch: {self.es_client.es_url}")
        print(f"  - LLM Model: {ollama_model}")
        print(f"  - Embedding Model: nomic-embed-text (768-dim)")
        print(f"  - Consumer: {consumer_name}")

    async def fetch_url_content(self, url: str) -> str:
        """Fetch and extract readable text from a URL"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove unwanted elements
                for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
                    element.decompose()

                # Extract text
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for phrase in ' '.join(lines).split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

                return text[:3000]  # Limit content size

        except Exception as e:
            print(f"    Warning: Could not fetch {url}: {e}")
            return ""

    async def analyze_sentiment(self, text: str, title: str) -> tuple[float, str]:
        """
        Analyze sentiment using LLM.

        Returns:
            (sentiment_score, sentiment_label)
        """
        if not text.strip():
            return 0.0, "Neutral"

        # Truncate for LLM
        max_chars = 1500
        truncated_text = text[:max_chars] if len(text) > max_chars else text

        prompt = f"""Analyze the sentiment of the following article/post about a brand.

Title: {title}

Content:
---
{truncated_text}
---

Provide your analysis in this exact format:
Sentiment: [Positive/Negative/Neutral]
Score: [number between -1.0 and 1.0, where -1.0 is very negative, 0.0 is neutral, 1.0 is very positive]
Reason: [one sentence explanation]
"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            response_text = response.content

            # Parse response
            sentiment_label = "Neutral"
            sentiment_score = 0.0

            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('Sentiment:'):
                    label = line.split(':', 1)[1].strip().lower()
                    if 'positive' in label:
                        sentiment_label = "Positive"
                    elif 'negative' in label:
                        sentiment_label = "Negative"
                    else:
                        sentiment_label = "Neutral"
                elif line.startswith('Score:'):
                    try:
                        score_str = line.split(':', 1)[1].strip()
                        score_str = ''.join(c for c in score_str if c.isdigit() or c in '.-')
                        sentiment_score = float(score_str)
                        sentiment_score = max(-1.0, min(1.0, sentiment_score))
                    except:
                        pass

            return sentiment_score, sentiment_label

        except Exception as e:
            print(f"    Warning: Sentiment analysis failed: {e}")
            return 0.0, "Neutral"

    def get_or_create_brand(self, session, brand_name: str) -> Brand:
        """Get existing brand or create new one"""
        # Try to find existing brand
        brand = session.query(Brand).filter(Brand.name == brand_name).first()

        if not brand:
            brand = Brand(name=brand_name)
            session.add(brand)
            session.commit()
            session.refresh(brand)
            print(f"    ✓ Created new brand: {brand_name}")

        return brand

    async def process_mention(self, message_id: str, mention_data: dict):
        """Process a single mention: fetch content, analyze sentiment, save to DB"""
        print(f"\n  Processing: {mention_data['title'][:60]}...")

        # Fetch content if not already present
        content = mention_data.get('content_snippet', '')
        if not content or len(content) < 100:
            if mention_data['source'] != 'hackernews':  # HN might not have external URL
                content = await self.fetch_url_content(mention_data['url'])

        # Analyze sentiment
        sentiment_score, sentiment_label = await self.analyze_sentiment(
            content,
            mention_data['title']
        )
        print(f"    → Sentiment: {sentiment_label} ({sentiment_score:+.2f})")

        # Phase 4: Generate embedding for semantic search
        embedding_text = self.embedding_service.prepare_text_for_embedding(
            mention_data['title'],
            content
        )
        embedding = await self.embedding_service.generate_embedding(embedding_text)
        if embedding:
            print(f"    → Embedding: Generated (768 dimensions)")
        else:
            print(f"    ⚠ Embedding: Failed to generate")

        # Phase 4: Extract entities
        entities = self.entity_service.extract_entities(
            mention_data['title'],
            content[:1000] if content else None  # Limit content for entity extraction
        )
        if entities:
            entity_count = sum(len(v) for v in entities.values())
            print(f"    → Entities: Extracted {entity_count} entities")
        else:
            print(f"    ⚠ Entities: None extracted")

        # Save to database
        with get_session(self.engine) as session:
            # Get or create brand
            brand = self.get_or_create_brand(session, mention_data['brand_name'])

            # Check if mention already exists (deduplication by URL)
            existing = session.query(Mention).filter(Mention.url == mention_data['url']).first()
            if existing:
                print(f"    ⚠ Mention already exists in database (ID: {existing.id})")
                return

            # Create mention (Phase 4: includes embedding and entities)
            mention = Mention(
                brand_id=brand.id,
                source=Source(mention_data['source']),
                title=mention_data['title'],
                url=mention_data['url'],
                content=content[:2000] if content else None,  # Store excerpt
                sentiment_score=sentiment_score,
                sentiment_label=SentimentLabel(sentiment_label),
                published_date=mention_data.get('published_date'),
                ingested_date=mention_data.get('ingested_at') or datetime.utcnow(),
                processed_date=datetime.utcnow(),
                author=mention_data.get('author'),
                points=mention_data.get('points'),
                # Phase 4: Semantic search and AI enhancements
                embedding=embedding,  # 768-dim vector for pgvector
                entities=entities  # Extracted named entities as JSON
            )

            session.add(mention)
            session.commit()
            session.refresh(mention)
            print(f"    ✓ Saved to database (Mention ID: {mention.id}, Brand ID: {brand.id})")

            # Index to Elasticsearch (Phase 4: includes entities)
            es_document = {
                "mention_id": mention.id,
                "brand_id": brand.id,
                "brand_name": brand.name,
                "source": mention_data['source'],
                "title": mention_data['title'],
                "url": mention_data['url'],
                "content": content[:2000] if content else None,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "published_date": mention_data.get('published_date'),
                "ingested_date": mention_data.get('ingested_at') or datetime.utcnow().isoformat(),
                "processed_date": datetime.utcnow().isoformat(),
                "author": mention_data.get('author'),
                "points": mention_data.get('points'),
                # Include enrichment metadata if present
                "domain": mention_data.get('domain'),
                "word_count": mention_data.get('word_count'),
                "reading_time_minutes": mention_data.get('reading_time_minutes'),
                "quality_score": mention_data.get('quality_score'),
                # Phase 4: Include entities for enhanced search
                "entities": entities if entities else {}
            }

            try:
                self.es_client.index_mention(mention.id, es_document, index_name=MENTIONS_INDEX)
                print(f"    ✓ Indexed to Elasticsearch")
            except Exception as e:
                print(f"    ⚠ Elasticsearch indexing failed: {e}")
                # Don't fail the whole process if ES indexing fails

        # Acknowledge message in Redis
        self.redis_client.acknowledge_enriched_message(self.consumer_group, message_id)

    async def run(self):
        """Main worker loop"""
        print(f"\n{'='*80}")
        print(f"  Sentiment Worker Running")
        print(f"  Consumer Group: {self.consumer_group}")
        print(f"  Consumer Name: {self.consumer_name}")
        print(f"  Input Stream: {self.redis_client.STREAM_MENTIONS_ENRICHED}")
        print(f"  Output: PostgreSQL + Elasticsearch")
        print(f"{'='*80}\n")

        try:
            for message_id, mention_data in self.redis_client.consume_enriched_mentions(
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
                block_ms=5000,
                count=1
            ):
                try:
                    await self.process_mention(message_id, mention_data)
                except Exception as e:
                    print(f"  ✗ Error processing mention: {e}")
                    # Don't acknowledge - message will be retried

        except KeyboardInterrupt:
            print("\n\n✓ Worker stopped by user")
        except Exception as e:
            print(f"\n✗ Worker error: {e}")
        finally:
            self.redis_client.close()

    def close(self):
        """Cleanup resources"""
        self.redis_client.close()
        self.engine.dispose()


async def main_async(args):
    """Async main function"""
    worker = SentimentWorker(
        redis_url=args.redis_url,
        database_url=args.database_url,
        elasticsearch_url=args.elasticsearch_url,
        ollama_model=args.model,
        consumer_name=args.consumer_name
    )

    await worker.run()
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 2/3: Sentiment Analysis Worker"
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=None,
        help="Redis connection URL"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL"
    )
    parser.add_argument(
        "--elasticsearch-url",
        type=str,
        default=None,
        help="Elasticsearch connection URL"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="Ollama model for sentiment analysis (default: llama3)"
    )
    parser.add_argument(
        "--consumer-name",
        type=str,
        default="sentiment-worker-1",
        help="Unique consumer name (default: sentiment-worker-1)"
    )

    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
