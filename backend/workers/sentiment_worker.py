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
from difflib import SequenceMatcher

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
from sqlmodel import select


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

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using SequenceMatcher.
        Returns a score between 0.0 and 1.0 (1.0 = identical)
        """
        return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()

    def calculate_relevance_score(self, title: str, content: str, brand_name: str) -> float:
        """
        Calculate relevance score (0-100) based on how relevant the mention is to the brand.

        Scoring criteria:
        - Brand in title: +40 points
        - Brand mentions in content: +10 points per mention (max 40)
        - Title length bonus: +20 points if reasonable length (prevents spam)
        """
        score = 0.0
        brand_lower = brand_name.lower()
        title_lower = title.lower()
        content_lower = (content or "").lower()

        # Check if brand is in title (strong signal)
        if brand_lower in title_lower:
            score += 40

        # Count brand mentions in content
        if content:
            mention_count = content_lower.count(brand_lower)
            # Cap at 4 mentions to avoid spam
            score += min(mention_count * 10, 40)

        # Title length check (reasonable titles are 20-200 chars)
        if 20 <= len(title) <= 200:
            score += 20

        return min(score, 100)  # Cap at 100

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
        if not text or not text.strip():
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
                fetched = await self.fetch_url_content(mention_data['url'])
                content = fetched if fetched else ''

        # Ensure content is never None
        content = content or ''

        # STEP 1: Calculate Relevance Score
        brand_name = mention_data.get('brand_name', '')
        relevance_score = self.calculate_relevance_score(
            mention_data['title'],
            content,
            brand_name
        )
        print(f"    → Relevance: {relevance_score:.0f}/100")

        # STEP 2: Filter Low Relevance (threshold: 50)
        if relevance_score < 50:
            print(f"    ⏭️  Skipped: Low relevance ({relevance_score:.0f} < 50)")
            self.redis_client.acknowledge_message(self.consumer_group, message_id)
            return

        # STEP 3: Check for Duplicate Titles (before saving to DB)
        brand_id = mention_data.get('brand_id')
        if brand_id:
            with get_session(self.engine) as session:
                # Check last 100 mentions for this brand
                recent_mentions = session.exec(
                    select(Mention)
                    .where(Mention.brand_id == brand_id)
                    .order_by(Mention.ingested_date.desc())
                    .limit(100)
                ).all()

                for existing_mention in recent_mentions:
                    similarity = self.calculate_title_similarity(
                        mention_data['title'],
                        existing_mention.title
                    )
                    if similarity > 0.85:
                        print(f"    ⏭️  Skipped: Duplicate title (similarity: {similarity:.2f})")
                        self.redis_client.acknowledge_message(self.consumer_group, message_id)
                        return

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
            # DEDUPLICATION - Check if mention already exists FIRST (before any processing)
            existing = session.exec(
                select(Mention).where(Mention.url == mention_data['url'])
            ).first()
            if existing:
                print(f"    ⏭️  Already exists (ID: {existing.id})")
                # Still acknowledge the message so it doesn't get reprocessed
                self.redis_client.acknowledge_message(self.consumer_group, message_id)
                return

            # Get brand_id from mention_data (required for user association)
            if 'brand_id' not in mention_data or not mention_data['brand_id']:
                print(f"    ⚠ No brand_id in mention data, skipping (legacy/malformed)")
                self.redis_client.acknowledge_message(self.consumer_group, message_id)
                return

            brand_id = mention_data['brand_id']
            # Verify brand exists
            brand = session.get(Brand, brand_id)
            if not brand:
                print(f"    ⚠ Brand ID {brand_id} not found, skipping mention")
                self.redis_client.acknowledge_message(self.consumer_group, message_id)
                return

            # Create mention (Phase 4: includes embedding and entities)
            mention = Mention(
                brand_id=brand_id,
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

        # Acknowledge message in Redis (raw stream)
        self.redis_client.acknowledge_message(self.consumer_group, message_id)

    async def run(self):
        """Main worker loop - reads from RAW stream for single-pass processing"""
        print(f"\n{'='*80}")
        print(f"  Sentiment Worker Running (Simplified Single-Pass)")
        print(f"  Consumer Group: {self.consumer_group}")
        print(f"  Consumer Name: {self.consumer_name}")
        print(f"  Input Stream: {self.redis_client.STREAM_MENTIONS_RAW}")
        print(f"  Output: PostgreSQL + Elasticsearch")
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
                except Exception as e:
                    print(f"  ✗ Error processing mention: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't acknowledge - message will be retried

        except KeyboardInterrupt:
            print("\n\n✓ Worker stopped by user")
        except Exception as e:
            print(f"\n✗ Worker error: {e}")
            import traceback
            traceback.print_exc()
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
