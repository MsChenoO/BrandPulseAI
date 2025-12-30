# Phase 5: WebSocket Router for Real-Time Updates
# Handles WebSocket connections with JWT authentication and real-time mention broadcasting

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from typing import Dict, Set, Optional
import json
import logging
from datetime import datetime
from sqlmodel import Session, select
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.database import User, get_engine
from services.auth_service import AuthService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"]
)

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://brandpulse:brandpulse_dev_password@localhost:5433/brandpulse"
)


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Features:
    - Multiple connections per user
    - Brand-specific subscriptions
    - Broadcast to specific users or brands
    - Connection tracking and cleanup
    """

    def __init__(self):
        # Active connections: {user_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[int, Set[WebSocket]] = {}

        # Brand subscriptions: {brand_id: {user_id1, user_id2, ...}}
        self.brand_subscriptions: Dict[int, Set[int]] = {}

        logger.info("WebSocket ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept a new WebSocket connection for a user.

        Args:
            websocket: WebSocket connection
            user_id: ID of the authenticated user
        """
        await websocket.accept()

        # Add connection to user's set
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

        logger.info(f"User {user_id} connected. Total connections: {self._count_connections()}")

        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            user_id: ID of the user
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Clean up brand subscriptions
                for brand_id in list(self.brand_subscriptions.keys()):
                    self.brand_subscriptions[brand_id].discard(user_id)
                    if not self.brand_subscriptions[brand_id]:
                        del self.brand_subscriptions[brand_id]

        logger.info(f"User {user_id} disconnected. Total connections: {self._count_connections()}")

    def subscribe_to_brand(self, user_id: int, brand_id: int):
        """
        Subscribe a user to brand-specific updates.

        Args:
            user_id: ID of the user
            brand_id: ID of the brand to subscribe to
        """
        if brand_id not in self.brand_subscriptions:
            self.brand_subscriptions[brand_id] = set()
        self.brand_subscriptions[brand_id].add(user_id)

        logger.info(f"User {user_id} subscribed to brand {brand_id}")

    def unsubscribe_from_brand(self, user_id: int, brand_id: int):
        """
        Unsubscribe a user from brand-specific updates.

        Args:
            user_id: ID of the user
            brand_id: ID of the brand to unsubscribe from
        """
        if brand_id in self.brand_subscriptions:
            self.brand_subscriptions[brand_id].discard(user_id)
            if not self.brand_subscriptions[brand_id]:
                del self.brand_subscriptions[brand_id]

        logger.info(f"User {user_id} unsubscribed from brand {brand_id}")

    async def send_to_user(self, user_id: int, message: dict):
        """
        Send a message to all connections of a specific user.

        Args:
            user_id: ID of the user
            message: Message to send (will be JSON serialized)
        """
        if user_id in self.active_connections:
            # Send to all user's connections
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)

    async def broadcast_to_brand(self, brand_id: int, message: dict):
        """
        Broadcast a message to all users subscribed to a brand.

        Args:
            brand_id: ID of the brand
            message: Message to broadcast (will be JSON serialized)
        """
        if brand_id in self.brand_subscriptions:
            subscribers = self.brand_subscriptions[brand_id].copy()
            for user_id in subscribers:
                await self.send_to_user(user_id, message)

    async def broadcast_to_all(self, message: dict):
        """
        Broadcast a message to all connected users.

        Args:
            message: Message to broadcast (will be JSON serialized)
        """
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)

    def _count_connections(self) -> int:
        """Count total number of active WebSocket connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": self._count_connections(),
            "unique_users": len(self.active_connections),
            "subscribed_brands": len(self.brand_subscriptions)
        }


# Global connection manager instance
manager = ConnectionManager()


# ============================================================================
# WebSocket Authentication
# ============================================================================

def authenticate_websocket(token: str, db: Session) -> Optional[User]:
    """
    Authenticate a WebSocket connection using JWT token.

    Args:
        token: JWT token from query parameter
        db: Database session

    Returns:
        User object if authentication successful, None otherwise
    """
    try:
        # Verify token and extract email
        email = AuthService.get_token_subject(token)

        if not email:
            return None

        # Find user
        user = db.exec(
            select(User).where(User.email == email)
        ).first()

        if not user or not user.is_active:
            return None

        return user

    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        return None


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time updates.

    Authentication:
        - Pass JWT token as query parameter: /ws/connect?token=<your_jwt_token>

    Message Types (Client → Server):
        - {"type": "ping"} - Heartbeat to keep connection alive
        - {"type": "subscribe", "brand_id": 123} - Subscribe to brand updates
        - {"type": "unsubscribe", "brand_id": 123} - Unsubscribe from brand updates

    Message Types (Server → Client):
        - {"type": "connection", "status": "connected"} - Connection established
        - {"type": "pong"} - Response to ping
        - {"type": "new_mention", "data": {...}} - New mention detected
        - {"type": "sentiment_update", "data": {...}} - Sentiment analysis update
        - {"type": "stats_update", "data": {...}} - Dashboard statistics update
        - {"type": "error", "message": "..."} - Error message
    """
    # Authenticate user
    engine = get_engine(DATABASE_URL)
    with Session(engine) as db:
        user = authenticate_websocket(token, db)

        if not user:
            logger.warning("WebSocket authentication failed")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = user.id
        logger.info(f"WebSocket authentication successful for user {user_id} ({user.email})")

    # Connect user
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle different message types
                if message_type == "ping":
                    # Heartbeat response
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_type == "subscribe":
                    # Subscribe to brand updates
                    brand_id = message.get("brand_id")
                    if brand_id:
                        manager.subscribe_to_brand(user_id, brand_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "brand_id": brand_id,
                            "message": f"Subscribed to brand {brand_id}",
                            "timestamp": datetime.utcnow().isoformat()
                        })

                elif message_type == "unsubscribe":
                    # Unsubscribe from brand updates
                    brand_id = message.get("brand_id")
                    if brand_id:
                        manager.unsubscribe_from_brand(user_id, brand_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "brand_id": brand_id,
                            "message": f"Unsubscribed from brand {brand_id}",
                            "timestamp": datetime.utcnow().isoformat()
                        })

                else:
                    # Unknown message type
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# ============================================================================
# WebSocket Stats Endpoint (HTTP)
# ============================================================================

@router.get("/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        Statistics about active WebSocket connections
    """
    return manager.get_stats()
