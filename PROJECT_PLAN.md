# BrandPulse: Enterprise AI Sentiment Analysis Platform

## 1. Project Overview
**BrandPulse** is a scalable, event-driven microservices platform designed to monitor brand reputation in real-time. It ingests data from public sources, analyzes sentiment using LLMs, indexes data for search, and triggers alerts on specific threat vectors.

**Primary Goals:**
* Showcase **AI Integration** (LLMs for classification/sentiment).
* Demonstrate **System Design** (Event-driven architecture, caching, search).
* Implement **DevOps Best Practices** (Docker, CI/CD, Documentation).

---

## 2. System Architecture
Event-driven microservices architecture with message streaming, designed for scalability and real-time processing.

### Architecture Diagram (High-Level):
```
[Ingestors] → [Redis Streams] → [Workers] → [Storage Layer] → [API] → [Frontend]
                                      ↓
                              [Alerting Service]
```

### Core Components:

**1. Platform-Specific Ingestors**
* *Sources:*
    * **Google News RSS** 
    * **HackerNews Algolia API** 
    * *Note: Twitter/X, Facebook, Instagram, Reddit excluded due to API cost/restrictions, maybe available in the future.*
* *Process:* Each ingestor polls sources for brand mentions, normalizes to common schema
* *Output:* Publishes `Mention` objects to Redis Streams
* *Schema:* `{mention_id, brand_name, source, title, url, content, author, published_date, ingested_date, points (for HN), raw_metadata}`

**2. Message Bus (Redis Streams)**
* *Technology:* Redis Streams for lightweight, persistent messaging
* *Streams:*
    * `mentions:raw` - Raw mentions from ingestors
    * `mentions:processed` - Enriched mentions post-analysis
    * `alerts:triggers` - Alert events
* *Benefits:* Decouples ingestion from processing; handles backpressure; enables replay

**3. Processing Workers (Consumer Groups)**
* *Worker Types:*
    * **Deduplication Worker:** Detects duplicate mentions using URL + title hashing
    * **Enrichment Worker:** Extracts domain, author metadata, calculates reading time
    * **Sentiment Worker:** LangChain + Ollama (OpenAI optional in later phases) for sentiment classification (-1.0 to +1.0)
    * **Embedding Worker:** Generates vector embeddings for semantic search (OpenAI or local)
* *Technology:* Python async workers consuming from Redis Streams
* *Output:* Writes enriched mentions to PostgreSQL + indexes to Elasticsearch + pgvector

**4. Storage & Search Layer**
* *Primary Database:* **PostgreSQL 15+** with pgvector extension
    * Tables: `brands`, `mentions`, `users`, `alert_rules`, `reports`
    * Indexes: B-tree on timestamps, GIN on JSONB, IVFFlat on vectors
* *Full-Text Search:* **Elasticsearch 8.x** (single-node for dev, cluster for prod)
    * Indexes mention title + content with analyzers
    * Supports fuzzy matching, phrase queries, aggregations
* *Vector Search:* **pgvector** (PostgreSQL extension, free)
    * Stores OpenAI/Ollama embeddings (1536 dimensions)
    * Cosine similarity search for "find similar mentions"
* *Hybrid Search:* Combines Elasticsearch score + vector similarity (RRF - Reciprocal Rank Fusion)

**5. Alerting & Anomaly Detection**
* *Rules Engine:* User-defined conditions (e.g., "sentiment < -0.6 AND source='reddit'")
* *Anomaly Detection:* Simple moving average on daily sentiment scores; alert on >2 std deviations
* *Notifications:* Email (SMTP), Slack webhooks, in-app notifications
* *Technology:* Celery Beat for scheduling, Redis as task broker

**6. API Layer (FastAPI)**
* *Endpoints:*
    * `POST /brands` - Create/track new brand
    * `GET /brands/{brand_id}/mentions` - Query mentions with filters
    * `POST /search` - Hybrid search (text + semantic)
    * `GET /brands/{brand_id}/sentiment-trend` - Time-series sentiment data
    * `WS /live-feed` - WebSocket for real-time mention stream
    * `POST /alerts/rules` - Configure alert rules
* *Auth:* JWT-based authentication
* *Docs:* Auto-generated OpenAPI/Swagger docs

**7. Presentation Layer (Next.js)**
* *Pages:*
    * Dashboard: Brand overview, sentiment trends (line charts)
    * Mentions Feed: Real-time list with filters (source, date, sentiment)
    * Search: Hybrid search interface
    * Alerts: Configure rules, view triggered alerts
* *Technology:* Next.js 14, TailwindCSS, Recharts, SWR for data fetching
* *Real-Time:* WebSocket client for live mention updates

**8. Reporting Service**
* *Reports:* Daily/weekly PDF summaries (brand sentiment, top mentions, trends)
* *Technology:* ReportLab (Python) for PDF generation
* *Scheduler:* Celery Beat cron jobs
* *Delivery:* Email attachments via SMTP

**9. Infrastructure**
* *Development:* Docker Compose (PostgreSQL, Redis, Elasticsearch, API, Workers, Frontend)
* *Production-Ready:* Kubernetes manifests
* *Secrets:* Environment variables + Docker secrets
* *Monitoring:* Prometheus + Grafana
* *CI/CD:* GitHub Actions (lint, test, build, deploy)

---

## 3. Technology Stack (Practical & Cost-Effective)

### Backend
* **Language:** Python 3.11+
* **Web Framework:** FastAPI 0.104+ (async, auto-docs, WebSocket support)
* **AI/LLM:**
    * LangChain 0.1+ (orchestration)
    * Ollama (local LLM, free - llama3, mistral)
    * OpenAI API (optional, for better embeddings - ~$0.0001/1K tokens)
* **Task Queue:** Celery 5.3+ with Redis broker
* **HTTP Client:** httpx (async), aiohttp
* **Data Parsing:** BeautifulSoup4, feedparser (RSS), PRAW (Reddit)

### Data Layer
* **Primary DB:** PostgreSQL 15+ with pgvector extension (vector storage)
* **Cache/Queue:** Redis 7+ (Streams, task broker, cache)
* **Search:** Elasticsearch 8.x (single-node dev, can scale)
* **ORM:** SQLModel (Pydantic + SQLAlchemy)
* **Migrations:** Alembic

### Frontend
* **Framework:** Next.js 14 (App Router, Server Components)
* **Language:** TypeScript 5+
* **Styling:** TailwindCSS 3.x
* **Charts:** Recharts (sentiment trends)
* **Data Fetching:** SWR or React Query
* **WebSocket:** Socket.io-client or native WebSocket API

### Infrastructure
* **Containerization:** Docker 24+, Docker Compose 2.x
* **Orchestration (Optional):** Kubernetes (Minikube for local, manifests for resume)
* **CI/CD:** GitHub Actions
* **Monitoring (Phase 6):** Prometheus, Grafana
* **Secrets:** Docker secrets, .env files (dev), Vault (prod concept)

### Development Tools
* **Linting:** Ruff (Python), ESLint (TypeScript)
* **Formatting:** Black (Python), Prettier (TypeScript)
* **Testing:** Pytest, Jest, React Testing Library
* **API Docs:** OpenAPI/Swagger (auto-generated by FastAPI)

---

## 4. Development Standards
* **Git Flow:**
    * `main`: Stable/Production.
    * `develop`: Staging/Integration.
    * `feature/xyz`: Active development.
* **Commits:** Conventional Commits (e.g., `feat: add scraper`, `fix: db timeout`).
* **Docs:** Updated `README.md` and API docs (Swagger/OpenAPI) required for every phase.

---

## 5. Implementation Roadmap

### Phase 1: Brand Mention Collection & Sentiment Analysis
**Goal:** Prove the core concept with a working CLI tool that collects from multiple sources

**Features:**
* Accept brand name as CLI input (e.g., "Google", "Tesla", "Python")
* **Multi-source ingestion:**
    * **Google News RSS** - Search news articles mentioning the brand
    * **HackerNews Algolia API** - Search tech community discussions
* Fetch 5-10 recent mentions per source (10-20 total)
* Parse article/post content with BeautifulSoup
* Sentiment analysis using Ollama (local LLM)
* Display brand sentiment report with source breakdown in terminal

**Tech Stack:** Python, httpx, feedparser, BeautifulSoup, LangChain, Ollama

**Deliverable:** CLI tool that generates sentiment reports from multiple sources

**Success Criteria:** Can analyze any brand from both Google News and HackerNews, showing source-specific breakdown

---

### Phase 2: Event-Driven Architecture + Persistence
**Goal:** Introduce message bus, refactor ingestors, persist data

**Features:**
* Redis Streams message bus (`mentions:raw` → `mentions:processed`)
* Refactor existing ingestors (Google News, HackerNews) to publish to Redis
* PostgreSQL database with SQLModel ORM
* Async processing workers (consume from Redis, write to DB)
* Docker Compose setup (PostgreSQL, Redis, App)
* Alembic migrations

**New Components:**
* `ingestors/google_news.py` - Publishes to Redis Streams
* `ingestors/hackernews.py` - Publishes to Redis Streams
* `workers/sentiment_worker.py` - Consumes messages, runs LLM
* `models/database.py` - SQLModel schemas

**Database Schema:**
```sql
CREATE TABLE brands (id, name, created_at);
CREATE TABLE mentions (
    id, brand_id, source, title, url, content,
    sentiment_score, sentiment_label,
    published_date, ingested_date, processed_date
);
```

**Deliverable:** `docker-compose up` → ingestors running → mentions in DB
```bash
docker-compose up -d
python -m ingestors.google_news --brand "Tesla"
python -m ingestors.hackernews --brand "Tesla"
# Data flows: Ingestor → Redis → Worker → PostgreSQL
```

**Success Criteria:** Mentions persist across restarts; can query DB for historical data

---

### Phase 3: Search Engine + REST API
**Goal:** Enable powerful search and expose data via API

**Features:**
* Elasticsearch integration (index mentions for full-text search)
* FastAPI REST API with OpenAPI docs
* Deduplication worker (hash URL+title to prevent duplicates)
* Enrichment worker (extract domain, calculate reading time)
* API endpoints:
    * `POST /brands` - Track new brand
    * `GET /brands/{id}/mentions` - Query with filters (date, source, sentiment)
    * `POST /search` - Full-text search across mentions
    * `GET /brands/{id}/sentiment-trend` - Time-series data
* JWT authentication (basic)

**Tech Stack:** FastAPI, Elasticsearch, Pydantic, python-jose (JWT)

**Example API Usage:**
```bash
# Create brand
curl -X POST http://localhost:8000/brands -d '{"name": "OpenAI"}'

# Get mentions
curl http://localhost:8000/brands/1/mentions?sentiment=negative&limit=20

# Search
curl -X POST http://localhost:8000/search -d '{"query": "lawsuit", "brand_id": 1}'
```

**Docker Compose:** Add Elasticsearch container

**Success Criteria:** Can search mentions by keyword; API returns filtered results in <200ms

---

### Phase 4: Semantic Search + AI Enhancements
**Goal:** Add vector embeddings for "find similar mentions" capability

**Features:**
* pgvector extension in PostgreSQL
* Embedding worker (generates vectors using Ollama or OpenAI)
* Hybrid search endpoint (combines Elasticsearch + vector similarity)
* Semantic search: "Find mentions similar to this one"
* Entity extraction worker (extract brands, people, locations from text)
* Improved sentiment analysis (multi-class: very negative, negative, neutral, positive, very positive)

**Tech Stack:** pgvector, sentence-transformers or OpenAI embeddings

**New API Endpoints:**
```bash
# Semantic search
POST /search/semantic
{
  "query": "negative reviews about customer service",
  "brand_id": 1,
  "limit": 10
}

# Find similar
GET /mentions/{id}/similar?limit=5
```

**Database Update:**
```sql
ALTER TABLE mentions ADD COLUMN embedding vector(1536);
CREATE INDEX ON mentions USING ivfflat (embedding vector_cosine_ops);
```

**Success Criteria:** Can find semantically similar mentions even with different wording

---

### Phase 5: Real-Time Dashboard + Live Feed
**Goal:** Build user-facing frontend with real-time updates

**Features:**
* Next.js 14 frontend (App Router, TypeScript, TailwindCSS)
* Pages:
    * Dashboard: Brand overview, sentiment KPIs, trend charts
    * Mentions Feed: Scrollable list with real-time updates
    * Search: Text + semantic search interface
    * Brand Management: Add/remove tracked brands
* WebSocket endpoint in FastAPI (`/ws/live-feed`)
* Real-time mention streaming (new mentions pushed to clients)
* Sentiment trend charts (Recharts - line/bar charts)
* Responsive design (mobile-friendly)

**Frontend Components:**
```
app/
├── dashboard/page.tsx         # Main dashboard
├── mentions/page.tsx          # Feed with infinite scroll
├── search/page.tsx            # Search interface
└── brands/[id]/page.tsx       # Brand detail page
```

**WebSocket Flow:**
```
Worker processes mention → Publishes to Redis pub/sub →
FastAPI WebSocket handler → Broadcasts to connected clients →
Next.js updates UI
```

**Deliverable:**
```bash
docker-compose up  # Starts all services including frontend
# Visit http://localhost:3000 - see live dashboard
```

**Success Criteria:** Dashboard updates in real-time as new mentions are ingested

---

### Phase 6: Alerting, Reporting & Production Readiness
**Goal:** Complete the platform with alerts, reports, and production deployment

**Features:**
* **Alerting Engine:**
    * User-defined rules (e.g., "Alert if sentiment < -0.6 on Reddit")
    * Anomaly detection (detect sentiment spikes/drops using rolling averages)
    * Notification channels: Email (SMTP), Slack webhooks
    * Alert history and management UI
* **Reporting Service:**
    * Weekly PDF reports (ReportLab)
    * CSV export for mentions
    * Scheduled email delivery (Celery Beat)
* **Production Features:**
    * Kubernetes manifests (deployment, service, ingress)
    * Helm chart (optional, for resume showcase)
    * Prometheus metrics (API latency, worker queue length, DB connections)
    * Grafana dashboards (system health, sentiment trends)
    * GitHub Actions CI/CD (lint, test, build Docker images, deploy)
    * Rate limiting (API endpoints)
    * Comprehensive logging (structured JSON logs)

**Tech Stack:** Celery Beat, ReportLab, Prometheus, Grafana, Kubernetes

**New Components:**
```
workers/alert_worker.py          # Evaluates rules
workers/anomaly_detector.py      # Statistical analysis
workers/report_generator.py      # PDF creation
k8s/
├── deployments/                 # K8s deployment manifests
├── services/                    # Service definitions
└── helm-chart/                  # Helm chart (optional)
```

**Deliverable:**
* Alerts trigger on negative sentiment
* Weekly PDF reports emailed to users
* K8s deployment (can run on Minikube)
* Monitoring dashboards showing system health

**Success Criteria:**
* Alert fires within 1 minute of trigger condition
* PDF report generated and emailed on schedule
* System runs reliably on Kubernetes

---

## Phase Progression Summary

| Phase | Core Focus | Key Deliverable | Tech Highlights |
|-------|-----------|----------------|-----------------|
| **1** | Core concept | CLI sentiment tool | Ollama, async Python |
| **2** | Event-driven architecture | Docker Compose setup | Redis Streams, PostgreSQL |
| **3** | Search & API | REST endpoints | Elasticsearch, FastAPI |
| **4** | AI enhancements | Semantic search | pgvector, embeddings |
| **5** | User interface | Real-time dashboard | Next.js, WebSockets |
| **6** | Production-ready | Alerts + monitoring | K8s, Prometheus, CI/CD |

