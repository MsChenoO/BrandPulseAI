# Phase 2: Redis Stream Utilities
# Handles publishing/consuming messages to/from Redis Streams

import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os


class RedisStreamClient:
    """Redis Streams client for event-driven architecture"""

    # Stream names
    STREAM_MENTIONS_RAW = "mentions:raw"
    STREAM_MENTIONS_PROCESSED = "mentions:processed"

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection URL (default: from env or localhost)
        """
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.redis_url = redis_url

    def publish_raw_mention(self, mention_data: Dict[str, Any]) -> str:
        """
        Publish a raw mention to the mentions:raw stream.

        Args:
            mention_data: Dictionary containing mention data

        Returns:
            Message ID from Redis
        """
        # Convert datetime objects to ISO strings
        serialized_data = self._serialize_data(mention_data)

        # Add metadata
        serialized_data["ingested_at"] = datetime.utcnow().isoformat()

        # Publish to stream
        message_id = self.client.xadd(
            self.STREAM_MENTIONS_RAW,
            serialized_data,
            maxlen=10000  # Keep last 10k messages
        )

        return message_id

    def consume_raw_mentions(
        self,
        consumer_group: str,
        consumer_name: str,
        block_ms: int = 5000,
        count: int = 10
    ):
        """
        Consume messages from mentions:raw stream using consumer groups.

        Args:
            consumer_group: Name of the consumer group
            consumer_name: Name of this consumer instance
            block_ms: Block for this many milliseconds if no messages
            count: Maximum number of messages to retrieve

        Yields:
            Tuples of (message_id, message_data)
        """
        # Create consumer group if it doesn't exist
        try:
            self.client.xgroup_create(
                self.STREAM_MENTIONS_RAW,
                consumer_group,
                id='0',
                mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            # Group already exists
            if "BUSYGROUP" not in str(e):
                raise

        while True:
            # Read messages
            messages = self.client.xreadgroup(
                consumer_group,
                consumer_name,
                {self.STREAM_MENTIONS_RAW: '>'},
                count=count,
                block=block_ms
            )

            if not messages:
                continue

            # Process messages
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    # Deserialize data
                    deserialized_data = self._deserialize_data(message_data)
                    yield message_id, deserialized_data

    def acknowledge_message(self, consumer_group: str, message_id: str):
        """
        Acknowledge that a message has been processed.

        Args:
            consumer_group: Name of the consumer group
            message_id: ID of the message to acknowledge
        """
        self.client.xack(self.STREAM_MENTIONS_RAW, consumer_group, message_id)

    def publish_processed_mention(self, mention_data: Dict[str, Any]) -> str:
        """
        Publish a processed mention to the mentions:processed stream.

        Args:
            mention_data: Dictionary containing processed mention data

        Returns:
            Message ID from Redis
        """
        serialized_data = self._serialize_data(mention_data)
        serialized_data["processed_at"] = datetime.utcnow().isoformat()

        message_id = self.client.xadd(
            self.STREAM_MENTIONS_PROCESSED,
            serialized_data,
            maxlen=10000
        )

        return message_id

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Convert data to Redis-compatible format (all strings)"""
        serialized = {}
        for key, value in data.items():
            if value is None:
                serialized[key] = ""
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = str(value)
        return serialized

    def _deserialize_data(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Convert Redis data back to Python types"""
        deserialized = {}
        for key, value in data.items():
            if value == "":
                deserialized[key] = None
            elif key in ["published_date", "ingested_at", "processed_at"]:
                try:
                    deserialized[key] = datetime.fromisoformat(value)
                except:
                    deserialized[key] = None
            elif key in ["points"]:
                try:
                    deserialized[key] = int(value)
                except:
                    deserialized[key] = None
            else:
                deserialized[key] = value
        return deserialized

    def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """Get information about a stream"""
        return self.client.xinfo_stream(stream_name)

    def close(self):
        """Close Redis connection"""
        self.client.close()
