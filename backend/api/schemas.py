# Phase 3: API Schemas (Pydantic Models)
# These define the structure of API requests and responses

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class SentimentLabelEnum(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class SourceEnum(str, Enum):
    """Data sources"""
    GOOGLE_NEWS = "google_news"
    HACKERNEWS = "hackernews"


# ============================================================================
# Brand Schemas
# ============================================================================

class BrandCreate(BaseModel):
    """Schema for creating a new brand"""
    name: str = Field(..., min_length=1, max_length=255, description="Brand name to monitor")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tesla"
            }
        }


class BrandResponse(BaseModel):
    """Schema for brand response"""
    id: int
    name: str
    created_at: datetime
    mention_count: Optional[int] = Field(None, description="Total number of mentions")

    class Config:
        from_attributes = True  # Allows conversion from SQLModel objects
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Tesla",
                "created_at": "2025-12-16T10:00:00",
                "mention_count": 42
            }
        }


class BrandList(BaseModel):
    """Schema for list of brands"""
    brands: List[BrandResponse]
    total: int


# ============================================================================
# Mention Schemas
# ============================================================================

class MentionResponse(BaseModel):
    """Schema for mention response"""
    id: int
    brand_id: int
    brand_name: Optional[str] = None
    source: SourceEnum
    title: str
    url: str
    content: Optional[str] = Field(None, description="Article content excerpt")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score from -1.0 to 1.0")
    sentiment_label: Optional[SentimentLabelEnum] = None
    published_date: Optional[datetime] = None
    ingested_date: datetime
    processed_date: Optional[datetime] = None
    author: Optional[str] = None
    points: Optional[int] = Field(None, description="HackerNews points")
    highlights: Optional[dict] = Field(None, description="Search result highlights")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "brand_id": 1,
                "source": "google_news",
                "title": "Tesla announces new Model 3",
                "url": "https://example.com/article",
                "content": "Tesla has announced...",
                "sentiment_score": 0.8,
                "sentiment_label": "Positive",
                "published_date": "2025-12-16T10:00:00",
                "ingested_date": "2025-12-16T10:05:00",
                "processed_date": "2025-12-16T10:06:00",
                "author": "John Doe",
                "points": None
            }
        }


class MentionList(BaseModel):
    """Schema for list of mentions"""
    mentions: List[MentionResponse]
    total: int
    page: int
    page_size: int


class MentionFilters(BaseModel):
    """Query parameters for filtering mentions"""
    source: Optional[SourceEnum] = None
    sentiment: Optional[SentimentLabelEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, le=100, description="Maximum results (max 100)")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


# ============================================================================
# Search Schemas
# ============================================================================

class SearchRequest(BaseModel):
    """Schema for search request"""
    query: str = Field(..., min_length=1, description="Search query text")
    brand_id: Optional[int] = Field(None, description="Filter by brand ID")
    source: Optional[SourceEnum] = Field(None, description="Filter by source")
    sentiment: Optional[SentimentLabelEnum] = Field(None, description="Filter by sentiment")
    limit: int = Field(default=20, le=100, description="Maximum results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "electric vehicle",
                "brand_id": 1,
                "source": "google_news",
                "sentiment": "Positive",
                "limit": 20
            }
        }


class SearchResult(BaseModel):
    """Schema for individual search result"""
    mention: MentionResponse
    score: float = Field(..., description="Elasticsearch relevance score")
    highlights: Optional[List[str]] = Field(None, description="Highlighted matching text")


class SearchResponse(BaseModel):
    """Schema for search response"""
    results: List[SearchResult]
    total: int
    took_ms: int = Field(..., description="Search time in milliseconds")


# ============================================================================
# Sentiment Trend Schemas
# ============================================================================

class SentimentTrendPoint(BaseModel):
    """Single data point in sentiment trend"""
    date: datetime
    average_score: float = Field(..., ge=-1.0, le=1.0)
    mention_count: int
    positive_count: int
    neutral_count: int
    negative_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-12-16T00:00:00",
                "average_score": 0.3,
                "mention_count": 15,
                "positive_count": 7,
                "neutral_count": 6,
                "negative_count": 2
            }
        }


class SentimentTrendResponse(BaseModel):
    """Schema for sentiment trend time series"""
    brand_id: int
    brand_name: str
    start_date: datetime
    end_date: datetime
    data_points: List[SentimentTrendPoint]
    overall_average: float

    class Config:
        json_schema_extra = {
            "example": {
                "brand_id": 1,
                "brand_name": "Tesla",
                "start_date": "2025-12-01T00:00:00",
                "end_date": "2025-12-16T00:00:00",
                "data_points": [],
                "overall_average": 0.25
            }
        }


# ============================================================================
# Generic Response Schemas
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
