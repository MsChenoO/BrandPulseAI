# Phase 1: Brand Mention Collection & Sentiment Analysis

import httpx
import feedparser
from bs4 import BeautifulSoup
from langchain_core.messages import HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import argparse
import asyncio


@dataclass
class Mention:
    """Data model for a brand mention from any source"""
    brand_name: str
    source: str  # "google_news" or "hackernews"
    title: str
    url: str
    content_snippet: str
    sentiment_score: float  # -1.0 to +1.0
    sentiment_label: str  # Positive/Neutral/Negative
    published_date: Optional[datetime]
    author: Optional[str] = None
    points: Optional[int] = None  # HackerNews points


# ============================================================================
# Google News RSS Ingestor
# ============================================================================

def fetch_google_news_mentions(brand_name: str, limit: int = 10) -> tuple[List[Dict], int]:
    """
    Fetch recent mentions of a brand from Google News RSS feed.

    Args:
        brand_name: The brand to search for
        limit: Maximum number of articles to fetch

    Returns:
        Tuple of (mention dictionaries list, total available count)
    """
    try:
        # Google News RSS search URL
        search_url = f"https://news.google.com/rss/search?q={brand_name}&hl=en-US&gl=US&ceid=US:en"

        print(f"  Searching Google News...")
        feed = feedparser.parse(search_url)

        total_available = len(feed.entries)
        mentions = []
        for entry in feed.entries[:limit]:
            mention = {
                "title": entry.title,
                "url": entry.link,
                "published_date": datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None,
                "source": "google_news"
            }
            mentions.append(mention)

        if total_available <= limit:
            print(f"  ✓ Found {total_available} articles mentioning '{brand_name}', analyzing all")
        else:
            print(f"  ✓ Found {total_available} articles mentioning '{brand_name}', analyzing {len(mentions)} most recent")

        return mentions, total_available

    except Exception as e:
        print(f"  ✗ Error fetching Google News: {e}")
        return [], 0


# ============================================================================
# HackerNews Ingestor
# ============================================================================

async def fetch_hackernews_mentions(brand_name: str, limit: int = 10) -> tuple[List[Dict], int]:
    """
    Fetch recent mentions of a brand from HackerNews using Algolia API.

    Args:
        brand_name: The brand to search for
        limit: Maximum number of stories to fetch

    Returns:
        Tuple of (mention dictionaries list, total available count)
    """
    try:
        # HackerNews Algolia Search API
        search_url = f"https://hn.algolia.com/api/v1/search?query={brand_name}&tags=story&hitsPerPage={limit}"

        print(f"  Searching HackerNews...")

        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        total_available = data.get('nbHits', 0)
        mentions = []
        for hit in data.get('hits', [])[:limit]:
            # Parse timestamp
            published_date = None
            if hit.get('created_at'):
                try:
                    published_date = datetime.fromisoformat(hit['created_at'].replace('Z', '+00:00'))
                except:
                    pass

            # Get URL (use story_url if available, otherwise HN item page)
            url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"

            mention = {
                "title": hit.get('title', ''),
                "url": url,
                "author": hit.get('author', 'unknown'),
                "published_date": published_date,
                "source": "hackernews",
                "content_snippet": hit.get('story_text', '')[:500] if hit.get('story_text') else '',
                "points": hit.get('points', 0)
            }
            mentions.append(mention)

        if total_available <= limit:
            print(f"  ✓ Found {total_available} articles mentioning '{brand_name}', analyzing all")
        else:
            print(f"  ✓ Found {total_available} articles mentioning '{brand_name}', analyzing {len(mentions)} most relevant")

        return mentions, total_available

    except Exception as e:
        print(f"  ✗ Error fetching HackerNews mentions: {e}")
        return [], 0


# ============================================================================
# Content Fetching & Parsing
# ============================================================================

async def fetch_url_content(url: str) -> str:
    """Fetch the HTML content of a given URL."""
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        try:
            response = await client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"    Warning: Could not fetch {url}: {e}")
            return ""


def extract_readable_text(html_content: str) -> str:
    """Extract readable text from HTML content using BeautifulSoup."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        script_or_style.decompose()

    # Get text
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for phrase in ' '.join(lines).split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


# ============================================================================
# Sentiment Analysis
# ============================================================================

async def analyze_sentiment(llm: BaseChatModel, text: str, title: str) -> tuple[float, str]:
    """
    Analyze sentiment of text using LLM.

    Returns:
        (sentiment_score, sentiment_label)
        sentiment_score: -1.0 (very negative) to +1.0 (very positive)
        sentiment_label: "Positive", "Neutral", or "Negative"
    """
    if not text.strip():
        return 0.0, "Neutral"

    # Truncate text for LLM processing
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
        response = await llm.ainvoke([HumanMessage(content=prompt)])
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
                    # Extract number from string (handle various formats)
                    score_str = ''.join(c for c in score_str if c.isdigit() or c in '.-')
                    sentiment_score = float(score_str)
                    # Clamp to [-1.0, 1.0]
                    sentiment_score = max(-1.0, min(1.0, sentiment_score))
                except:
                    pass

        return sentiment_score, sentiment_label

    except Exception as e:
        print(f"    Warning: Sentiment analysis failed: {e}")
        return 0.0, "Neutral"


# ============================================================================
# Multi-Source Processing
# ============================================================================

async def process_mentions(raw_mentions: List[Dict], brand_name: str, llm: BaseChatModel) -> List[Mention]:
    """
    Process raw mentions: fetch content and analyze sentiment.

    Args:
        raw_mentions: List of raw mention dicts from ingestors
        brand_name: The brand being analyzed
        llm: Language model for sentiment analysis

    Returns:
        List of processed Mention objects with sentiment scores
    """
    processed_mentions = []

    for i, raw in enumerate(raw_mentions, 1):
        print(f"    [{i}/{len(raw_mentions)}] Processing: {raw['title'][:60]}...")

        # Fetch article content (skip for HackerNews posts that already have content)
        if raw['source'] == 'hackernews' and raw.get('content_snippet'):
            content = raw['content_snippet']
        else:
            html_content = await fetch_url_content(raw['url'])
            content = extract_readable_text(html_content)

        # Analyze sentiment
        sentiment_score, sentiment_label = await analyze_sentiment(
            llm, content, raw['title']
        )

        # Create Mention object
        mention = Mention(
            brand_name=brand_name,
            source=raw['source'],
            title=raw['title'],
            url=raw['url'],
            content_snippet=content[:200] if content else "",
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            published_date=raw.get('published_date'),
            author=raw.get('author'),
            points=raw.get('points')
        )

        processed_mentions.append(mention)
        print(f"      → Sentiment: {sentiment_label} ({sentiment_score:+.2f})")

    return processed_mentions


# ============================================================================
# Report Generation
# ============================================================================

def generate_report(mentions: List[Mention], brand_name: str, total_counts: Dict[str, int]) -> None:
    """Generate and print a brand sentiment report."""

    if not mentions:
        print(f"\n❌ No mentions found for '{brand_name}'")
        return

    # Group by source
    by_source = {}
    for mention in mentions:
        if mention.source not in by_source:
            by_source[mention.source] = []
        by_source[mention.source].append(mention)

    # Calculate overall stats
    sentiment_counts = Counter(m.sentiment_label for m in mentions)
    avg_score = sum(m.sentiment_score for m in mentions) / len(mentions)

    # Print report
    print("\n" + "=" * 80)
    print(f"  BRAND SENTIMENT REPORT: {brand_name}")
    print("=" * 80)

    # Scanning statistics
    total_found = sum(total_counts.values())
    total_analyzed = len(mentions)

    print(f"\n🔍 Scanning Statistics:")
    print(f"   Total Articles Found: {total_found}")
    print(f"   Articles Analyzed: {total_analyzed}")
    print(f"\n   By Source:")
    for source, source_mentions in by_source.items():
        source_name = "Google News" if source == "google_news" else "HackerNews"
        source_total = total_counts.get(source, 0)
        print(f"   • {source_name}: {len(source_mentions)} analyzed ({source_total} total available)")

    print(f"\n📊 Overall Sentiment ({len(mentions)} mentions analyzed)")
    print(f"   Average Sentiment Score: {avg_score:+.2f}")
    print(f"   Breakdown:")
    for label in ["Positive", "Neutral", "Negative"]:
        count = sentiment_counts[label]
        percentage = (count / len(mentions)) * 100
        print(f"     • {label}: {count} ({percentage:.1f}%)")

    # Per-source breakdown
    print(f"\n📰 By Source:")
    for source, source_mentions in by_source.items():
        source_name = "Google News" if source == "google_news" else "HackerNews"
        source_counts = Counter(m.sentiment_label for m in source_mentions)
        source_avg = sum(m.sentiment_score for m in source_mentions) / len(source_mentions)

        print(f"\n   {source_name}: {len(source_mentions)} mentions (avg: {source_avg:+.2f})")
        for label in ["Positive", "Neutral", "Negative"]:
            count = source_counts[label]
            if count > 0:
                print(f"     • {label}: {count}")

    # Recent mentions
    print(f"\n📝 Recent Mentions:")
    for mention in mentions[:5]:  # Show top 5
        source_icon = "🗞️ " if mention.source == "google_news" else "🟠"
        print(f"\n   {source_icon} [{mention.sentiment_label}] {mention.title[:70]}")
        print(f"      {mention.url}")
        if mention.content_snippet:
            print(f"      \"{mention.content_snippet[:100]}...\"")

    print("\n" + "=" * 80 + "\n")


# ============================================================================
# Main Function
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="BrandPulse Phase 1: Multi-source brand sentiment analysis"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Brand name to monitor (e.g., 'Tesla', 'Google', 'Apple')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of mentions to fetch per source (default: 5)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="Ollama model to use for sentiment analysis (default: llama3)"
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="news,hackernews",
        help="Comma-separated list of sources: news,hackernews (default: both)"
    )

    args = parser.parse_args()

    brand_name = args.brand
    limit_per_source = args.limit
    sources = args.sources.lower().split(',')

    print(f"\n{'='*80}")
    print(f"  BrandPulse - Phase 1: Brand Sentiment Analysis")
    print(f"{'='*80}")
    print(f"  Brand: {brand_name}")
    print(f"  Sources: {', '.join(sources)}")
    print(f"  Limit per source: {limit_per_source}")
    print(f"  LLM Model: {args.model}")
    print(f"{'='*80}\n")

    # Collect mentions from all sources
    raw_mentions = []
    total_counts = {}

    if 'news' in sources:
        print("📰 Collecting from Google News...")
        news_mentions, news_total = fetch_google_news_mentions(brand_name, limit_per_source)
        raw_mentions.extend(news_mentions)
        total_counts['google_news'] = news_total

    if 'hackernews' in sources:
        print("\n🟠 Collecting from HackerNews...")
        hn_mentions, hn_total = await fetch_hackernews_mentions(brand_name, limit_per_source)
        raw_mentions.extend(hn_mentions)
        total_counts['hackernews'] = hn_total

    if not raw_mentions:
        print("\n❌ No mentions found. Try adjusting your search parameters.")
        return

    print(f"\n✓ Collected {len(raw_mentions)} total mentions")

    # Initialize LLM
    print(f"\n🤖 Analyzing sentiment with {args.model}...")
    llm = ChatOllama(model=args.model)

    # Process mentions and analyze sentiment
    processed_mentions = await process_mentions(raw_mentions, brand_name, llm)

    # Generate report
    generate_report(processed_mentions, brand_name, total_counts)


if __name__ == "__main__":
    asyncio.run(main())
