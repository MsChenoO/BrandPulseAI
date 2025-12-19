#!/usr/bin/env python3
"""
BrandPulse Enrichment Worker Runner

This script runs the enrichment worker that:
- Consumes deduplicated mentions from Redis stream: mentions:deduplicated
- Enriches with metadata: domain, reading time, quality score, word count
- Publishes enriched mentions back to the stream

Usage:
    python run_enrichment_worker.py
    python run_enrichment_worker.py --consumer-name enrichment-worker-2
"""

import sys
sys.path.append('.')

from workers.enrichment_worker import main

if __name__ == "__main__":
    exit(main())
