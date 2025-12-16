# BrandPulseAI
Enterprise-grade AI Sentiment Analysis Platform

## Overview
**BrandPulseAI** is a scalable, event-driven platform for real-time brand reputation monitoring. It ingests data from public sources, analyzes sentiment using LLMs, and provides actionable insights through an intelligent alerting system.

## Current Status: Phase 2 In Progress 🚧
**Phase 1**: ✅ Multi-source brand sentiment monitoring (CLI)
**Phase 2**: 🚧 Event-driven architecture with Redis Streams and PostgreSQL persistence

## Features (Phase 1)
- 🏷️ **Brand-focused monitoring** - Track any brand across multiple sources
- 📰 **Google News RSS** - Automatic collection of news articles mentioning your brand
- 🟠 **HackerNews integration** - Tech community discussions via Algolia API 
- 🤖 **AI-powered sentiment analysis** - Ollama (local LLM) analyzes each mention
- 📊 **Multi-source aggregation** - Combined sentiment report across all sources
- 🖥️ **CLI interface** - Easy-to-use command-line tool
- ⚡ **Async processing** - Fast, concurrent processing of mentions

## Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- [Docker](https://www.docker.com/) & Docker Compose (for Phase 2+)
- pip (Python package manager)

## Installation

### 1. Install Ollama
Download and install Ollama from [https://ollama.ai](https://ollama.ai)

Pull the llama3 model:
```bash
ollama pull llama3
```

### 2. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

## Usage

### Basic Usage
Monitor brand sentiment from Google News and HackerNews:
```bash
python backend/main.py --brand "Tesla" --limit 5
```

### Options
```bash
# Monitor specific brand
python backend/main.py --brand "OpenAI"

# Limit mentions per source
python backend/main.py --brand "Google" --limit 10

# Choose specific sources (news, hackernews, or both)
python backend/main.py --brand "Apple" --sources news,hackernews

# HackerNews only (great for tech brands)
python backend/main.py --brand "Python" --sources hackernews --limit 5

# Google News only
python backend/main.py --brand "Tesla" --sources news --limit 10

# Use different Ollama model
python backend/main.py --brand "Microsoft" --model llama2
```

### Example Output
```
================================================================================
  BrandPulse - Phase 1: Brand Sentiment Analysis
================================================================================
  Brand: OpenAI
  Sources: news
  Limit per source: 3
  LLM Model: llama3
================================================================================

📰 Collecting from Google News...
  ✓ Found 3 articles from Google News

🤖 Analyzing sentiment with llama3...
    [1/3] Processing: Oracle is already underwater on its 'astonishing' $300bn OpenAI deal
      → Sentiment: Negative (-0.70)
    [2/3] Processing: Leak confirms OpenAI is preparing ads on ChatGPT...
      → Sentiment: Neutral (+0.05)

================================================================================
  BRAND SENTIMENT REPORT: OpenAI
================================================================================

📊 Overall Summary (3 total mentions)
   Average Sentiment Score: -0.22
   Breakdown:
     • Positive: 0 (0.0%)
     • Neutral: 2 (66.7%)
     • Negative: 1 (33.3%)

📰 By Source:
   Google News: 3 mentions (avg: -0.22)

📝 Recent Mentions:
   🗞️  [Negative] Oracle is already underwater on its 'astonishing' $300bn OpenAI deal
      https://news.google.com/...
```

---

## Phase 2: Event-Driven Architecture

Phase 2 introduces a **production-grade event-driven architecture** with message queues and persistent storage.

### Architecture

```
[Ingestors] → [Redis Streams] → [Workers] → [PostgreSQL]
```

### Features (Phase 2)
- 📮 **Redis Streams** - Event-driven message bus for decoupled processing
- 🗄️ **PostgreSQL** - Persistent storage for brands and mentions
- 🔄 **Async Workers** - Background workers for sentiment analysis
- 🐳 **Docker Compose** - Containerized infrastructure
- 📊 **Database Migrations** - Alembic for schema management

### Setup Phase 2

#### 1. Start Infrastructure
```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### 3. Set Up Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (default values work with docker-compose)
```

#### 4. Initialize Database
```bash
# Run migrations (creates tables)
cd backend
alembic upgrade head
```

### Usage Phase 2

Phase 2 uses a **pipeline architecture**: Ingestors → Redis → Workers → Database

#### Step 1: Start the Sentiment Worker

The worker processes mentions from Redis and saves them to PostgreSQL:

```bash
# Terminal 1: Start the sentiment worker
cd backend
python workers/sentiment_worker.py

# You should see:
# ✓ Sentiment Worker initialized
# Waiting for messages from: mentions:raw
```

#### Step 2: Run Ingestors

In a separate terminal, run the ingestors to collect and publish mentions:

```bash
# Terminal 2: Run both ingestors for a brand
cd backend
python run_ingestor.py --brand "Tesla" --limit 5

# Or run individual ingestors:
python ingestors/google_news.py --brand "OpenAI" --limit 10
python ingestors/hackernews.py --brand "Python" --limit 10
```

#### Workflow

1. **Ingestors** fetch mentions and publish to Redis Streams
2. **Worker** consumes messages, fetches content, analyzes sentiment
3. **Database** persists processed mentions with sentiment scores
4. Data survives restarts and is queryable

### Querying the Database

```bash
# Connect to PostgreSQL
docker exec -it brandpulse-postgres psql -U brandpulse -d brandpulse

# View brands
SELECT * FROM brands;

# View mentions with sentiment
SELECT id, brand_id, source, title, sentiment_label, sentiment_score
FROM mentions
ORDER BY ingested_date DESC
LIMIT 10;

# Get sentiment summary for a brand
SELECT
    sentiment_label,
    COUNT(*) as count,
    AVG(sentiment_score) as avg_score
FROM mentions
WHERE brand_id = 1
GROUP BY sentiment_label;
```

### Stopping Services

```bash
# Stop containers (data persists)
docker-compose stop

# Stop and remove containers + volumes (deletes data)
docker-compose down -v
```

---

## Project Structure
```
BrandPulseAI/
├── backend/
│   ├── main.py                     
│   ├── run_ingestor.py              
│   ├── requirements.txt             
│   ├── alembic.ini                 
│   ├── alembic/                    
│   ├── ingestors/                   
│   │   ├── google_news.py         
│   │   └── hackernews.py            
│   ├── workers/                  
│   │   └── sentiment_worker.py      
│   ├── models/                      
│   │   └── database.py             
│   └── shared/                      
│       └── redis_client.py          
├── docker-compose.yml               
├── .env.example                    
├── docs/                            
├── PROJECT_PLAN.md                 
└── README.md                        
```

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

### 📋 Phase 3: Search & API Layer
- Elasticsearch full-text search
- FastAPI REST endpoints
- Deduplication & enrichment workers
- JWT authentication

### 🎨 Phase 4: Semantic Search + AI Enhancements
- pgvector for embeddings
- Hybrid search (text + semantic)
- Entity extraction

### 🎯 Phase 5: Real-Time Dashboard + Live Feed
- Next.js frontend
- WebSocket live updates
- Sentiment trend charts

### 🔔 Phase 6: Alerting & Production Readiness
- Rules engine & anomaly detection
- Email/Slack notifications
- PDF reports
- Kubernetes deployment

## Technology Stack

### Phase 1 & 2
- **Language:** Python 3.11+
- **Web Scraping:** httpx, BeautifulSoup4, feedparser
- **LLM:** LangChain + Ollama (llama3, mistral)
- **Database:** PostgreSQL 15+ with SQLModel ORM
- **Message Queue:** Redis 7+ (Streams)
- **Migrations:** Alembic
- **Infrastructure:** Docker & Docker Compose

## Contributing
This is a portfolio project demonstrating enterprise-grade architecture and AI integration.

## License
MIT
