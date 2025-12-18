# Phase 3: FastAPI Dependencies
# Reusable components for dependency injection

from typing import Generator
from sqlmodel import Session
from elasticsearch import Elasticsearch
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_engine


# ============================================================================
# Database Dependencies
# ============================================================================

def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Usage in endpoint:
        @app.get("/example")
        def example(db: Session = Depends(get_db_session)):
            # Use db here
            pass

    The session is automatically closed after the request.
    """
    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
    )

    # Create engine and session
    engine = get_engine(database_url)
    session = Session(engine)

    try:
        yield session  # Provide session to the endpoint
    finally:
        session.close()  # Automatically close after request


# ============================================================================
# Elasticsearch Dependencies
# ============================================================================

def get_elasticsearch() -> Generator[Elasticsearch, None, None]:
    """
    Dependency that provides an Elasticsearch client.

    Usage in endpoint:
        @app.get("/search")
        def search(es: Elasticsearch = Depends(get_elasticsearch)):
            # Use es here
            pass

    The connection is automatically closed after the request.
    """
    # Get Elasticsearch URL from environment
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # Create client
    es = Elasticsearch([es_url])

    try:
        yield es  # Provide client to the endpoint
    finally:
        es.close()  # Automatically close after request


# ============================================================================
# Pagination Helper
# ============================================================================

class PaginationParams:
    """
    Reusable pagination parameters.

    Usage:
        @app.get("/items")
        def get_items(pagination: PaginationParams = Depends()):
            limit = pagination.limit
            offset = pagination.offset
    """

    def __init__(
        self,
        limit: int = 20,
        offset: int = 0
    ):
        self.limit = min(limit, 100)  # Cap at 100
        self.offset = max(offset, 0)  # No negative offsets


# ============================================================================
# Error Handlers
# ============================================================================

class NotFoundError(Exception):
    """Custom exception for 404 Not Found"""
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class BadRequestError(Exception):
    """Custom exception for 400 Bad Request"""
    def __init__(self, message: str = "Bad request"):
        self.message = message
        super().__init__(self.message)
