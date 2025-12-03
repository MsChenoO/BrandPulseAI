# Phase 2: Database Models
# SQLModel schemas for PostgreSQL

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class Source(str, Enum):
    """Supported data sources"""
    GOOGLE_NEWS = "google_news"
    HACKERNEWS = "hackernews"


# ============================================================================
# Database Tables
# ============================================================================

class Brand(SQLModel, table=True):
    """Brand entity - represents a brand being monitored"""
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    mentions: List["Mention"] = Relationship(back_populates="brand")


class Mention(SQLModel, table=True):
    """Mention entity - represents a single brand mention from any source"""
    __tablename__ = "mentions"

    id: Optional[int] = Field(default=None, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id", index=True)

    # Source metadata
    source: Source = Field(index=True)
    title: str = Field(max_length=500)
    url: str = Field(max_length=1000, unique=True)
    content: Optional[str] = Field(default=None)

    # Sentiment analysis results
    sentiment_score: Optional[float] = Field(default=None)  # -1.0 to +1.0
    sentiment_label: Optional[SentimentLabel] = Field(default=None)

    # Timestamps
    published_date: Optional[datetime] = Field(default=None, index=True)
    ingested_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    processed_date: Optional[datetime] = Field(default=None)

    # Additional metadata (source-specific)
    author: Optional[str] = Field(default=None, max_length=255)
    points: Optional[int] = Field(default=None)  # HackerNews points

    # Relationship
    brand: Brand = Relationship(back_populates="mentions")


# ============================================================================
# Database Engine Setup
# ============================================================================

from sqlmodel import create_engine, Session
from sqlalchemy.pool import NullPool

def get_engine(database_url: str):
    """Create database engine with connection pooling"""
    # Use NullPool for development to avoid connection issues
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL query logging
        poolclass=NullPool
    )
    return engine


def create_db_and_tables(engine):
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)


def get_session(engine) -> Session:
    """Get a database session"""
    return Session(engine)
