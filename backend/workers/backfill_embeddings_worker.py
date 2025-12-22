#!/usr/bin/env python3
"""
Phase 4: Backfill Embeddings Worker

Processes existing mentions in the database that don't have embeddings or entities.
Generates embeddings and extracts entities for these mentions.
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_engine, Mention
from shared.embedding_service import EmbeddingService
from shared.entity_extraction_service import EntityExtractionService
from shared.elasticsearch_client import ElasticsearchClient, MENTIONS_INDEX
from sqlmodel import Session, select


class BackfillWorker:
    """Worker to backfill embeddings and entities for existing mentions"""

    def __init__(
        self,
        database_url: str = None,
        elasticsearch_url: str = None,
        ollama_model: str = "llama3",
        batch_size: int = 10,
        dry_run: bool = False
    ):
        """
        Initialize the backfill worker.

        Args:
            database_url: PostgreSQL connection URL
            elasticsearch_url: Elasticsearch connection URL
            ollama_model: Ollama model name for entity extraction
            batch_size: Number of mentions to process in each batch
            dry_run: If True, don't save changes to database
        """
        # Database setup
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
            )
        self.engine = get_engine(database_url)
        self.batch_size = batch_size
        self.dry_run = dry_run

        # Phase 4 services
        self.embedding_service = EmbeddingService()
        self.entity_service = EntityExtractionService(model=ollama_model)

        # Elasticsearch (optional - for updating indexed entities)
        self.es_client = None
        if elasticsearch_url or os.getenv("ELASTICSEARCH_URL"):
            try:
                self.es_client = ElasticsearchClient(es_url=elasticsearch_url)
                print("  ✓ Elasticsearch client initialized (will update entities)")
            except Exception as e:
                print(f"  ⚠ Elasticsearch not available: {e}")

        print(f"✓ Backfill Worker initialized")
        print(f"  - Database: {database_url}")
        print(f"  - Batch size: {batch_size}")
        print(f"  - Dry run: {dry_run}")
        print(f"  - Ollama model: {ollama_model}")

    def get_mentions_needing_backfill(self, session: Session) -> list[Mention]:
        """Get mentions that need embeddings or entities"""
        # Find mentions without embeddings OR without entities
        query = select(Mention).where(
            (Mention.embedding.is_(None)) | (Mention.entities.is_(None))
        ).limit(self.batch_size)

        mentions = session.exec(query).all()
        return list(mentions)

    async def process_mention(self, session: Session, mention: Mention) -> bool:
        """
        Process a single mention: generate embedding and extract entities.

        Args:
            session: Database session
            mention: Mention to process

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n  Processing Mention ID {mention.id}:")
            print(f"    Title: {mention.title[:60]}...")

            updated = False

            # Generate embedding if missing
            if mention.embedding is None:
                embedding_text = self.embedding_service.prepare_text_for_embedding(
                    mention.title,
                    mention.content
                )
                embedding = await self.embedding_service.generate_embedding(embedding_text)

                if embedding:
                    mention.embedding = embedding
                    updated = True
                    print(f"    ✓ Generated embedding (768 dimensions)")
                else:
                    print(f"    ⚠ Failed to generate embedding")
            else:
                print(f"    → Embedding already exists")

            # Extract entities if missing
            if mention.entities is None:
                entities = self.entity_service.extract_entities(
                    mention.title,
                    mention.content[:1000] if mention.content else None
                )

                if entities:
                    mention.entities = entities
                    updated = True
                    entity_count = sum(len(v) for v in entities.values())
                    print(f"    ✓ Extracted {entity_count} entities")

                    # Update Elasticsearch if available
                    if self.es_client and not self.dry_run:
                        try:
                            # Update just the entities field in Elasticsearch
                            self.es_client.es.update(
                                index=MENTIONS_INDEX,
                                id=str(mention.id),
                                body={
                                    "doc": {
                                        "entities": entities
                                    }
                                }
                            )
                            print(f"    ✓ Updated entities in Elasticsearch")
                        except Exception as e:
                            print(f"    ⚠ Elasticsearch update failed: {e}")
                else:
                    print(f"    ⚠ Failed to extract entities")
            else:
                print(f"    → Entities already exist")

            # Save to database
            if updated:
                if not self.dry_run:
                    session.add(mention)
                    session.commit()
                    print(f"    ✓ Saved to database")
                else:
                    print(f"    [DRY RUN] Would save to database")

            return True

        except Exception as e:
            print(f"    ✗ Error processing mention {mention.id}: {e}")
            session.rollback()
            return False

    async def run(self):
        """Main backfill loop"""
        print(f"\n{'='*80}")
        print(f"  Phase 4: Backfill Embeddings & Entities Worker")
        print(f"{'='*80}\n")

        total_processed = 0
        total_succeeded = 0
        total_failed = 0

        try:
            while True:
                with Session(self.engine) as session:
                    # Get next batch
                    mentions = self.get_mentions_needing_backfill(session)

                    if not mentions:
                        print("\n✓ No more mentions need backfilling!")
                        break

                    print(f"\nProcessing batch of {len(mentions)} mentions...")

                    # Process each mention
                    for mention in mentions:
                        success = await self.process_mention(session, mention)
                        total_processed += 1

                        if success:
                            total_succeeded += 1
                        else:
                            total_failed += 1

                    # If batch was smaller than batch_size, we're done
                    if len(mentions) < self.batch_size:
                        break

        except KeyboardInterrupt:
            print("\n\n⚠ Backfill interrupted by user")
        except Exception as e:
            print(f"\n✗ Backfill error: {e}")
        finally:
            # Print summary
            print(f"\n{'='*80}")
            print(f"  Backfill Summary")
            print(f"{'='*80}")
            print(f"  Total processed: {total_processed}")
            print(f"  Succeeded: {total_succeeded}")
            print(f"  Failed: {total_failed}")
            print(f"  Dry run: {self.dry_run}")
            print(f"{'='*80}\n")

        return total_succeeded


async def main_async(args):
    """Async main function"""
    worker = BackfillWorker(
        database_url=args.database_url,
        elasticsearch_url=args.elasticsearch_url,
        ollama_model=args.model,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    # Show stats before starting
    with Session(worker.engine) as session:
        total = session.exec(select(Mention)).all()
        without_embeddings = session.exec(
            select(Mention).where(Mention.embedding.is_(None))
        ).all()
        without_entities = session.exec(
            select(Mention).where(Mention.entities.is_(None))
        ).all()

        print(f"\nDatabase Statistics:")
        print(f"  Total mentions: {len(total)}")
        print(f"  Without embeddings: {len(without_embeddings)}")
        print(f"  Without entities: {len(without_entities)}")

    # Ask for confirmation if not dry run
    if not args.dry_run and not args.yes:
        response = input(f"\nProceed with backfill? (y/n): ")
        if response.lower() != 'y':
            print("Backfill cancelled")
            return 1

    # Run backfill
    succeeded = await worker.run()
    return 0 if succeeded > 0 else 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 4: Backfill Embeddings & Entities Worker"
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
        help="Elasticsearch connection URL (optional)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="Ollama model for entity extraction (default: llama3)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of mentions to process per batch (default: 10)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't save changes to database (test mode)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    exit(main())
