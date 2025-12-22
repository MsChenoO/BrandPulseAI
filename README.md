# BrandPulseAI
Enterprise-grade AI Sentiment Analysis Platform

## Overview
**BrandPulseAI** is a scalable, event-driven platform for real-time brand reputation monitoring. It ingests data from public sources, analyzes sentiment using LLMs, and provides actionable insights through an intelligent alerting system.

## Current Status: Phase 4 Complete! 🎉
**Phase 1**: ✅ Multi-source brand sentiment monitoring (CLI)
**Phase 2**: ✅ Event-driven architecture with Redis Streams and PostgreSQL
**Phase 3**: ✅ Elasticsearch + REST API with full pipeline integration
**Phase 4**: ✅ Semantic search with pgvector + AI-powered entity extraction

## Features
- 🏷️ **Brand-focused monitoring** - Track any brand across multiple sources
- 📰 **Google News RSS** - Automatic collection of news articles mentioning your brand
- 🟠 **HackerNews integration** - Tech community discussions via Algolia API
- 🤖 **AI-powered sentiment analysis** - Ollama (local LLM) analyzes each mention
- 📊 **Multi-source aggregation** - Combined sentiment report across all sources
- ⚡ **Async processing** - Fast, concurrent processing of mentions
- 🔍 **Semantic search** - Find mentions by meaning, not just keywords (pgvector)
- 🎯 **Hybrid search** - Combines keyword and semantic search with weighted scoring
- 🏷️ **Entity extraction** - Auto-extracts people, organizations, products, technologies
- 🔄 **Vector embeddings** - 768-dimensional embeddings for all mentions
- 📈 **RESTful API** - 10+ endpoints including semantic and hybrid search

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- [Docker](https://www.docker.com/) & Docker Compose
---

## Development Roadmap

### ✅ Phase 1: Brand Mention Collection & Sentiment Analysis (COMPLETED)
- Multi-source ingestion (Google News + HackerNews)
- Brand-focused search
- Sentiment analysis via LLM
- Aggregated reporting

### ✅ Phase 2: Event-Driven Architecture + Persistence (COMPLETED)
- Redis Streams message bus
- PostgreSQL database with SQLModel ORM
- Docker Compose setup
- Async processing workers
- Database migrations with Alembic

### ✅ Phase 3: Search Engine + REST API (COMPLETED)
- Elasticsearch 8.11.0 full-text search
- FastAPI REST API with 7 endpoints
- Deduplication worker (content hashing)
- Enrichment worker (metadata extraction)
- Dual storage architecture (PostgreSQL + Elasticsearch)
- Sentiment trend analytics
- Auto-generated API documentation (Swagger/OpenAPI)
- Complete pipeline integration

### ✅ Phase 4: Semantic Search + AI Enhancements (COMPLETED)
- **pgvector integration** - PostgreSQL with vector similarity search
- **Semantic search API** - Find mentions by meaning using 768-dimensional embeddings
- **Hybrid search** - Weighted combination of keyword + semantic search
- **Entity extraction** - LLM-based extraction of people, organizations, products, technologies, locations
- **Backfill worker** - Process existing mentions to add embeddings and entities
- **Vector similarity index** - IVFFlat index with cosine distance for fast searches
- **Ollama embeddings** - nomic-embed-text model (768 dimensions)
- **100% data coverage** - All mentions have embeddings and extracted entities
- **Performance optimized** - ~800ms semantic search, ~200ms hybrid search
- **Production ready** - Comprehensive API with filtering, scoring, and analytics

### 🎯 Phase 5: Real-Time Dashboard + Live Feed
- Next.js frontend
- WebSocket live updates
- Sentiment trend charts

### 🔔 Phase 6: Alerting & Production Readiness
- Rules engine & anomaly detection
- Email/Slack notifications
- PDF reports
- Kubernetes deployment
---

## Technology Stack

### Phases 1-4
- **Language:** Python 3.11+
- **Web Scraping:** httpx, BeautifulSoup4, feedparser
- **LLM:** LangChain + Ollama (llama3, mistral, nomic-embed-text)
- **Database:** PostgreSQL 15+ with SQLModel ORM + pgvector extension
- **Vector Search:** pgvector 0.5.1 (768-dimensional embeddings)
- **Message Queue:** Redis 7+ (Streams)
- **Search Engine:** Elasticsearch 8.11.0
- **REST API:** FastAPI + Uvicorn
- **Validation:** Pydantic
- **Migrations:** Alembic
- **Infrastructure:** Docker & Docker Compose
- **Embeddings:** Ollama nomic-embed-text (768 dimensions)
- **Entity Extraction:** LLM-based NER (Named Entity Recognition)

## Contributing
This is a portfolio project demonstrating enterprise-grade architecture and AI integration.

## License
MIT
