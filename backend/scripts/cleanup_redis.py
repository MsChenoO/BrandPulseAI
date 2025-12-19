#!/usr/bin/env python3
# Clean up Redis streams and sets for testing

import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.redis_client import RedisStreamClient

redis_client = RedisStreamClient()

print("Cleaning up Redis...")
print("="*80)

# Delete streams
streams = [
    redis_client.STREAM_MENTIONS_RAW,
    redis_client.STREAM_MENTIONS_DEDUPLICATED,
    redis_client.STREAM_MENTIONS_PROCESSED
]

for stream in streams:
    try:
        redis_client.client.delete(stream)
        print(f"✓ Deleted stream: {stream}")
    except Exception as e:
        print(f"  (Stream {stream} didn't exist)")

# Delete hash set
try:
    redis_client.client.delete(redis_client.SET_MENTION_HASHES)
    print(f"✓ Deleted set: {redis_client.SET_MENTION_HASHES}")
except Exception as e:
    print(f"  (Set didn't exist)")

print("="*80)
print("✓ Redis cleaned up successfully!")

redis_client.close()
