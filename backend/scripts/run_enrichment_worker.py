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
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.enrichment_worker import main

if __name__ == "__main__":
    exit(main())
