# BrandPulseAI
Enterprise-grade AI Sentiment Analysis Platform

## Overview
**BrandPulseAI** is a scalable, event-driven platform for real-time brand reputation monitoring. It ingests data from public sources, analyzes sentiment using LLMs, and provides actionable insights through an intelligent alerting system.

## Current Status: Phase 1 Complete ✅
Phase 1 implements **multi-source brand sentiment monitoring** with Google News and HackerNews integration.

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

## Project Structure
```
BrandPulseAI/
├── backend/
│   ├── main.py              # Phase 1: CLI sentiment analyzer
│   ├── requirements.txt     # Python dependencies
│   └── venv/               # Virtual environment
├── frontend/               
├── infra/                 
├── docs/                   # Documentation
├── PROJECT_PLAN.md         
└── README.md              
```

## Development Roadmap

### ✅ Phase 1: Brand Mention Collection & Sentiment Analysis (COMPLETED)
- Multi-source ingestion (Google News + HackerNews)
- Brand-focused search
- Sentiment analysis via LLM
- Aggregated reporting

### 🔄 Phase 2: Event-Driven Architecture + Persistence (NEXT)
- Redis Streams message bus
- PostgreSQL database
- Docker Compose setup
- Async processing workers

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

## Technology Stack (Phase 1)
- **Language:** Python 3.11+
- **Async HTTP:** httpx
- **HTML Parsing:** BeautifulSoup4
- **RSS Parsing:** feedparser
- **HackerNews API:** Algolia API (free, no authentication)
- **LLM Framework:** LangChain
- **Local LLM:** Ollama (llama3, mistral)

## Contributing
This is a portfolio project demonstrating enterprise-grade architecture and AI integration.

## License
MIT
