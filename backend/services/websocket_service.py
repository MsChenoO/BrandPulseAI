# Phase 5: WebSocket Broadcasting Service
# Provides functions to broadcast real-time updates to connected WebSocket clients

import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Service for broadcasting real-time updates via WebSocket.

    This is a singleton service that can be imported and used throughout
    the application to send real-time updates to connected clients.
    """

    def __init__(self):
        self._manager = None

    def set_manager(self, manager):
        """
        Set the connection manager instance.

        Args:
            manager: ConnectionManager instance from websocket router
        """
        self._manager = manager
        logger.info("WebSocket service initialized with connection manager")

    @property
    def manager(self):
        """Get the connection manager."""
        if self._manager is None:
            logger.warning("WebSocket manager not initialized")
        return self._manager

    async def broadcast_new_mention(
        self,
        mention_data: Dict[str, Any],
        brand_id: Optional[int] = None
    ):
        """
        Broadcast a new mention to relevant users.

        Args:
            mention_data: Mention data to broadcast
            brand_id: Optional brand ID to broadcast to specific subscribers
        """
        if not self.manager:
            return

        message = {
            "type": "new_mention",
            "data": mention_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Always broadcast to all users (users can filter on client side)
        await self.manager.broadcast_to_all(message)
        logger.info(f"Broadcasted new mention (brand_id: {brand_id}) to all users")

    async def broadcast_sentiment_update(
        self,
        sentiment_data: Dict[str, Any],
        brand_id: Optional[int] = None
    ):
        """
        Broadcast sentiment analysis update.

        Args:
            sentiment_data: Sentiment analysis data
            brand_id: Optional brand ID to broadcast to specific subscribers
        """
        if not self.manager:
            return

        message = {
            "type": "sentiment_update",
            "data": sentiment_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if brand_id:
            await self.manager.broadcast_to_brand(brand_id, message)
            logger.info(f"Broadcasted sentiment update for brand {brand_id}")
        else:
            await self.manager.broadcast_to_all(message)
            logger.info("Broadcasted sentiment update to all users")

    async def broadcast_stats_update(
        self,
        stats_data: Dict[str, Any],
        user_id: Optional[int] = None,
        brand_id: Optional[int] = None
    ):
        """
        Broadcast dashboard statistics update.

        Args:
            stats_data: Statistics data to broadcast
            user_id: Optional user ID to send to specific user
            brand_id: Optional brand ID to broadcast to subscribers
        """
        if not self.manager:
            return

        message = {
            "type": "stats_update",
            "data": stats_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if user_id:
            # Send to specific user
            await self.manager.send_to_user(user_id, message)
            logger.info(f"Sent stats update to user {user_id}")
        elif brand_id:
            # Broadcast to brand subscribers
            await self.manager.broadcast_to_brand(brand_id, message)
            logger.info(f"Broadcasted stats update for brand {brand_id}")
        else:
            # Broadcast to all users
            await self.manager.broadcast_to_all(message)
            logger.info("Broadcasted stats update to all users")

    async def send_notification(
        self,
        notification_data: Dict[str, Any],
        user_id: Optional[int] = None
    ):
        """
        Send a notification to a user or all users.

        Args:
            notification_data: Notification data
            user_id: Optional user ID to send to specific user
        """
        if not self.manager:
            return

        message = {
            "type": "notification",
            "data": notification_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        if user_id:
            await self.manager.send_to_user(user_id, message)
            logger.info(f"Sent notification to user {user_id}")
        else:
            await self.manager.broadcast_to_all(message)
            logger.info("Broadcasted notification to all users")

    def get_connection_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get WebSocket connection statistics.

        Returns:
            Connection statistics or None if manager not initialized
        """
        if not self.manager:
            return None

        return self.manager.get_stats()


# Global WebSocket service instance
websocket_service = WebSocketService()


# ============================================================================
# Helper Functions for Easy Broadcasting
# ============================================================================

async def broadcast_new_mention(mention_data: Dict[str, Any], brand_id: Optional[int] = None):
    """
    Helper function to broadcast a new mention.

    Usage:
        from services.websocket_service import broadcast_new_mention

        await broadcast_new_mention({
            "id": mention.id,
            "title": mention.title,
            "content": mention.content,
            "sentiment": mention.sentiment_label,
            "brand_id": mention.brand_id
        }, brand_id=mention.brand_id)
    """
    await websocket_service.broadcast_new_mention(mention_data, brand_id)


async def broadcast_sentiment_update(sentiment_data: Dict[str, Any], brand_id: Optional[int] = None):
    """
    Helper function to broadcast a sentiment update.

    Usage:
        from services.websocket_service import broadcast_sentiment_update

        await broadcast_sentiment_update({
            "brand_id": brand.id,
            "positive_count": 10,
            "neutral_count": 5,
            "negative_count": 2
        }, brand_id=brand.id)
    """
    await websocket_service.broadcast_sentiment_update(sentiment_data, brand_id)


async def broadcast_stats_update(
    stats_data: Dict[str, Any],
    user_id: Optional[int] = None,
    brand_id: Optional[int] = None
):
    """
    Helper function to broadcast statistics update.

    Usage:
        from services.websocket_service import broadcast_stats_update

        await broadcast_stats_update({
            "total_mentions": 100,
            "positive_count": 60,
            "neutral_count": 30,
            "negative_count": 10
        })
    """
    await websocket_service.broadcast_stats_update(stats_data, user_id, brand_id)
