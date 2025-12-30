#!/usr/bin/env python3
"""
Add test mentions to see the dashboard features working.
This bypasses the ingestion pipeline and adds mentions directly to the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_engine, get_session, Brand, Mention, Source, SentimentLabel
from datetime import datetime, timedelta
import random


def add_test_mentions():
    """Add test mentions for existing brands"""

    # Database setup
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
    )
    engine = get_engine(database_url)
    session = get_session(engine)

    # Get all brands
    brands = session.query(Brand).all()

    if not brands:
        print("❌ No brands found. Please add brands through the UI first.")
        return

    print(f"\n✓ Found {len(brands)} brand(s)")

    # Test data templates
    news_templates = [
        {
            "title": "{brand} announces major partnership with leading tech company",
            "content": "In a groundbreaking move, {brand} has formed a strategic partnership that will revolutionize the industry.",
            "sentiment": ("Positive", 0.8)
        },
        {
            "title": "{brand} faces criticism over recent product launch",
            "content": "Users have expressed disappointment with {brand}'s latest offering, citing quality concerns.",
            "sentiment": ("Negative", -0.6)
        },
        {
            "title": "{brand} releases quarterly earnings report",
            "content": "The company reported steady growth in Q4, meeting analyst expectations.",
            "sentiment": ("Neutral", 0.1)
        },
        {
            "title": "{brand} unveils innovative new feature",
            "content": "Tech enthusiasts are excited about {brand}'s latest innovation, calling it a game-changer.",
            "sentiment": ("Positive", 0.7)
        },
        {
            "title": "{brand} addresses customer concerns",
            "content": "In response to recent feedback, {brand} has committed to improving customer service.",
            "sentiment": ("Neutral", 0.2)
        },
        {
            "title": "{brand} wins industry award",
            "content": "{brand} has been recognized for excellence in innovation and customer satisfaction.",
            "sentiment": ("Positive", 0.9)
        },
        {
            "title": "{brand} stock drops amid market uncertainty",
            "content": "Shares of {brand} fell today as investors react to broader market trends.",
            "sentiment": ("Negative", -0.4)
        },
        {
            "title": "{brand} expands to new markets",
            "content": "The company announced plans to enter three new international markets next quarter.",
            "sentiment": ("Positive", 0.6)
        },
    ]

    total_added = 0

    for brand in brands:
        print(f"\n📊 Adding mentions for: {brand.name} (Brand ID: {brand.id})")

        # Add 5-10 random mentions per brand
        num_mentions = random.randint(5, 10)

        for i in range(num_mentions):
            template = random.choice(news_templates)

            # Randomize published date within last 30 days
            days_ago = random.randint(0, 30)
            published_date = datetime.utcnow() - timedelta(days=days_ago)

            # Create unique URL
            source = random.choice([Source.GOOGLE_NEWS, Source.HACKERNEWS])
            url = f"https://example.com/{brand.name.lower().replace(' ', '-')}/article-{brand.id}-{i}"

            sentiment_label, sentiment_score = template["sentiment"]

            mention = Mention(
                brand_id=brand.id,
                source=source,
                title=template["title"].format(brand=brand.name),
                url=url,
                content=template["content"].format(brand=brand.name),
                sentiment_score=sentiment_score,
                sentiment_label=SentimentLabel(sentiment_label),
                published_date=published_date,
                ingested_date=datetime.utcnow(),
                processed_date=datetime.utcnow(),
                author="Test Author" if random.random() > 0.5 else None,
                points=random.randint(10, 100) if source == Source.HACKERNEWS else None
            )

            session.add(mention)
            total_added += 1

        print(f"   ✓ Added {num_mentions} mentions")

    # Commit all mentions
    session.commit()
    session.close()

    print(f"\n{'='*60}")
    print(f"✅ Successfully added {total_added} test mentions")
    print(f"{'='*60}")
    print("\n📈 Refresh your dashboard to see the data!")


if __name__ == "__main__":
    add_test_mentions()
