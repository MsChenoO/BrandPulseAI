#!/usr/bin/env python3
"""
Cleanup script to remove duplicate mentions from the database.

Removes duplicates based on:
1. Exact URL matches (same article from different sources)
2. Similar titles (>85% similarity) for the same brand

Keeps the oldest mention (first ingested) and removes newer duplicates.
"""

import sys
import os
from datetime import datetime
from difflib import SequenceMatcher

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_engine, Mention, Brand, get_session
from sqlmodel import select


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles."""
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()


def cleanup_url_duplicates(session):
    """Remove mentions with duplicate URLs (exact matches)."""
    print("\n🔍 Checking for URL duplicates...")

    # Get all mentions ordered by ingested_date
    all_mentions = session.exec(
        select(Mention).order_by(Mention.ingested_date.asc())
    ).all()

    seen_urls = {}
    duplicates_removed = 0

    for mention in all_mentions:
        if mention.url in seen_urls:
            # This is a duplicate
            original_id = seen_urls[mention.url]
            print(f"  ❌ Removing duplicate URL: {mention.title[:60]}... (ID: {mention.id}, original: {original_id})")
            session.delete(mention)
            duplicates_removed += 1
        else:
            # First time seeing this URL
            seen_urls[mention.url] = mention.id

    session.commit()
    print(f"  ✓ Removed {duplicates_removed} URL duplicates")
    return duplicates_removed


def cleanup_title_duplicates(session, similarity_threshold=0.85):
    """Remove mentions with very similar titles for the same brand."""
    print(f"\n🔍 Checking for title duplicates (similarity > {similarity_threshold})...")

    # Get all brands
    brands = session.exec(select(Brand)).all()
    total_duplicates_removed = 0

    for brand in brands:
        # Get all mentions for this brand, ordered by ingested_date
        mentions = session.exec(
            select(Mention)
            .where(Mention.brand_id == brand.id)
            .order_by(Mention.ingested_date.asc())
        ).all()

        if len(mentions) <= 1:
            continue

        print(f"\n  Brand: {brand.name} ({len(mentions)} mentions)")

        kept_mentions = []
        duplicates_removed = 0

        for mention in mentions:
            is_duplicate = False

            # Compare with all mentions we're keeping
            for kept in kept_mentions:
                similarity = calculate_title_similarity(mention.title, kept.title)
                if similarity > similarity_threshold:
                    # This is a duplicate
                    print(f"    ❌ Removing similar title (similarity: {similarity:.2f})")
                    print(f"       Original: {kept.title[:60]}...")
                    print(f"       Duplicate: {mention.title[:60]}... (ID: {mention.id})")
                    session.delete(mention)
                    duplicates_removed += 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept_mentions.append(mention)

        if duplicates_removed > 0:
            print(f"  ✓ Removed {duplicates_removed} title duplicates for {brand.name}")
            total_duplicates_removed += duplicates_removed

    session.commit()
    print(f"\n  ✓ Total title duplicates removed: {total_duplicates_removed}")
    return total_duplicates_removed


def main():
    """Main cleanup process."""
    print("="*80)
    print("  BrandPulse AI - Duplicate Cleanup Script")
    print("="*80)

    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
    )
    engine = get_engine(database_url)

    with get_session(engine) as session:
        # Step 1: Remove exact URL duplicates
        url_dups = cleanup_url_duplicates(session)

        # Step 2: Remove similar title duplicates
        title_dups = cleanup_title_duplicates(session, similarity_threshold=0.85)

        # Summary
        total_removed = url_dups + title_dups
        print("\n" + "="*80)
        print(f"  ✅ Cleanup Complete!")
        print(f"  Total duplicates removed: {total_removed}")
        print(f"    - URL duplicates: {url_dups}")
        print(f"    - Title duplicates: {title_dups}")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()
