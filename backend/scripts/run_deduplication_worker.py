#!/usr/bin/env python3
"""
BrandPulse Deduplication Worker Runner

This script runs the deduplication worker that:
- Consumes raw mentions from Redis stream: mentions:raw
- Calculates hash from URL + title
- Filters out duplicates using Redis Set
- Publishes unique mentions to: mentions:deduplicated

Usage:
    python run_deduplication_worker.py
    python run_deduplication_worker.py --consumer-name dedup-worker-2
"""

import sys
sys.path.append('.')

from workers.deduplication_worker import main

if __name__ == "__main__":
    exit(main())
