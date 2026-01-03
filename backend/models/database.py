# Phase 2-4: Database Models
# SQLModel schemas for PostgreSQL

from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import ForeignKey


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

class User(SQLModel, table=True):
    """User entity - for authentication and authorization"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, max_length=255)
    username: str = Field(index=True, unique=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    brands: List["Brand"] = Relationship(back_populates="user")


class Brand(SQLModel, table=True):
    """Brand entity - represents a brand being monitored"""
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    user_id: int = Field(sa_column=Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    mentions: List["Mention"] = Relationship(
        back_populates="brand",
        sa_relationship_kwargs={"cascade": "all, delete", "passive_deletes": True}
    )
    user: "User" = Relationship(back_populates="brands")


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

    # Phase 4: Semantic Search & AI Enhancements
    embedding: Optional[Any] = Field(default=None, sa_column=Column(Vector(768)))  # 768-dim vector for nomic-embed-text
    entities: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Extracted entities

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
