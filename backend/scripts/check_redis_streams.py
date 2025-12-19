#!/usr/bin/env python3
# Check Redis streams status

import sys
sys.path.append('.')

from shared.redis_client import RedisStreamClient

redis_client = RedisStreamClient()

print("Redis Streams Status")
print("="*80)

# Check raw mentions stream
try:
    raw_info = redis_client.get_stream_info(redis_client.STREAM_MENTIONS_RAW)
    raw_length = raw_info['length']
    print(f"\n✓ {redis_client.STREAM_MENTIONS_RAW}")
    print(f"  Length: {raw_length} messages")
except Exception as e:
    print(f"\n✗ {redis_client.STREAM_MENTIONS_RAW}: {e}")

# Check deduplicated mentions stream
try:
    dedup_info = redis_client.get_stream_info(redis_client.STREAM_MENTIONS_DEDUPLICATED)
    dedup_length = dedup_info['length']
    print(f"\n✓ {redis_client.STREAM_MENTIONS_DEDUPLICATED}")
    print(f"  Length: {dedup_length} messages")
except Exception as e:
    print(f"\n✗ {redis_client.STREAM_MENTIONS_DEDUPLICATED}: Stream doesn't exist yet or empty")

# Check processed mentions stream
try:
    proc_info = redis_client.get_stream_info(redis_client.STREAM_MENTIONS_PROCESSED)
    proc_length = proc_info['length']
    print(f"\n✓ {redis_client.STREAM_MENTIONS_PROCESSED}")
    print(f"  Length: {proc_length} messages")
except Exception as e:
    print(f"\n✗ {redis_client.STREAM_MENTIONS_PROCESSED}: Stream doesn't exist yet or empty")

# Check hash set
try:
    hash_count = redis_client.client.scard(redis_client.SET_MENTION_HASHES)
    print(f"\n✓ {redis_client.SET_MENTION_HASHES}")
    print(f"  Unique hashes: {hash_count}")
except Exception as e:
    print(f"\n✗ {redis_client.SET_MENTION_HASHES}: {e}")

print("\n" + "="*80)

redis_client.close()
