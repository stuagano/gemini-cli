"""
WebSocket Handler for streaming agent responses
Manages real-time communication between TypeScript CLI and Python agents
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Set
import asyncio
import json
import logging
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types"""
    # Connection management
    INIT = "init"
    CONNECTED = "connected"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    
    # Request/Response
    REQUEST = "request"
    RESPONSE = "response"
    STREAM_REQUEST = "stream_request"
    STREAM_CHUNK = "stream_chunk"
    STREAM_COMPLETE = "stream_complete"
    
    # Events
    EVENT = "event"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    
    # Errors
    ERROR = "error"

@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""
    type: MessageType
    data: Any
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "type": self.type.value,
            "data": self.data,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp
        }

@dataclass
class StreamChunk:
    """Chunk of streaming data"""
    content: str
    index: int
    total: Optional[int] = None
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None

class ConnectionState:
    """Manages connection state for a client"""
    
    def __init__(self, client_id: str, websocket: WebSocket):
        self.client_id = client_id
        self.websocket = websocket
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.subscriptions: Set[str] = set()
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.metadata: Dict[str, Any] = {}
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_subscription(self, topic: str):
        """Add a subscription"""
        self.subscriptions.add(topic)
    
    def remove_subscription(self, topic: str):
        """Remove a subscription"""
        self.subscriptions.discard(topic)
    
    def is_subscribed(self, topic: str) -> bool:
        """Check if subscribed to a topic"""
        return topic in self.subscriptions
    
    async def cleanup(self):
        """Clean up connection resources"""
        # Cancel active streams
        for stream_id, task in self.active_streams.items():
            if not task.done():
                task.cancel()
        self.active_streams.clear()
        
        # Clear subscriptions
        self.subscriptions.clear()

class WebSocketHandler:
    """Handles WebSocket connections and messaging"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionState] = {}
        self.event_subscribers: Dict[str, Set[str]] = {}  # topic -> client_ids
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.stats = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
    
    async def handle_connection(self, websocket: WebSocket) -> str:
        """Handle a new WebSocket connection"""
        client_id = str(uuid.uuid4())
        await websocket.accept()
        
        # Create connection state
        state = ConnectionState(client_id, websocket)
        self.connections[client_id] = state
        self.stats["total_connections"] += 1
        
        logger.info(f"WebSocket connection established: {client_id}")
        
        # Send connection confirmation
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.CONNECTED,
                data={
                    "client_id": client_id,
                    "session_id": str(uuid.uuid4()),
                    "capabilities": self._get_capabilities()
                }
            )
        )
        
        return client_id
    
    async def handle_disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.connections:
            state = self.connections[client_id]
            await state.cleanup()
            
            # Remove from all subscriptions
            for topic in list(state.subscriptions):
                self._unsubscribe(client_id, topic)
            
            del self.connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def process_message(self, client_id: str, raw_message: str) -> None:
        """Process incoming WebSocket message"""
        try:
            self.stats["messages_received"] += 1
            
            # Parse message
            data = json.loads(raw_message)
            message_type = MessageType(data.get("type"))
            
            # Update activity
            if client_id in self.connections:
                self.connections[client_id].update_activity()
            
            # Route message to appropriate handler
            handlers = {
                MessageType.INIT: self._handle_init,
                MessageType.REQUEST: self._handle_request,
                MessageType.STREAM_REQUEST: self._handle_stream_request,
                MessageType.SUBSCRIBE: self._handle_subscribe,
                MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
                MessageType.PING: self._handle_ping,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(client_id, data)
            else:
                await self._send_error(client_id, f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError as e:
            await self._send_error(client_id, f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            await self._send_error(client_id, str(e))
            self.stats["errors"] += 1
    
    async def send_message(self, client_id: str, message: WebSocketMessage) -> bool:
        """Send message to a specific client"""
        if client_id not in self.connections:
            logger.warning(f"Attempted to send to disconnected client: {client_id}")
            return False
        
        try:
            state = self.connections[client_id]
            await state.websocket.send_json(message.to_dict())
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to {client_id}: {e}")
            await self.handle_disconnect(client_id)
            return False
    
    async def broadcast(self, message: WebSocketMessage, topic: Optional[str] = None):
        """Broadcast message to all clients or topic subscribers"""
        if topic and topic in self.event_subscribers:
            client_ids = self.event_subscribers[topic].copy()
        else:
            client_ids = list(self.connections.keys())
        
        # Send to all clients concurrently
        tasks = [self.send_message(client_id, message) for client_id in client_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.debug(f"Broadcast to {success_count}/{len(client_ids)} clients")
    
    async def stream_response(
        self,
        client_id: str,
        request_id: str,
        generator: AsyncGenerator[Any, None]
    ):
        """Stream response chunks to client"""
        if client_id not in self.connections:
            return
        
        state = self.connections[client_id]
        
        # Create streaming task
        async def stream_task():
            try:
                chunk_index = 0
                async for chunk in generator:
                    if client_id not in self.connections:
                        break
                    
                    # Send chunk
                    await self.send_message(
                        client_id,
                        WebSocketMessage(
                            type=MessageType.STREAM_CHUNK,
                            data={
                                "request_id": request_id,
                                "chunk": StreamChunk(
                                    content=chunk,
                                    index=chunk_index,
                                    is_final=False
                                ).to_dict() if not isinstance(chunk, dict) else chunk
                            }
                        )
                    )
                    chunk_index += 1
                
                # Send completion
                await self.send_message(
                    client_id,
                    WebSocketMessage(
                        type=MessageType.STREAM_COMPLETE,
                        data={"request_id": request_id, "total_chunks": chunk_index}
                    )
                )
                
            except asyncio.CancelledError:
                logger.info(f"Stream {request_id} cancelled")
            except Exception as e:
                logger.error(f"Error in stream {request_id}: {e}")
                await self._send_error(client_id, f"Stream error: {e}")
            finally:
                # Clean up
                if request_id in state.active_streams:
                    del state.active_streams[request_id]
        
        # Start streaming task
        task = asyncio.create_task(stream_task())
        state.active_streams[request_id] = task
    
    # Message handlers
    async def _handle_init(self, client_id: str, data: Dict[str, Any]):
        """Handle initialization message"""
        if client_id in self.connections:
            state = self.connections[client_id]
            state.metadata.update(data.get("metadata", {}))
            
            await self.send_message(
                client_id,
                WebSocketMessage(
                    type=MessageType.RESPONSE,
                    data={
                        "status": "initialized",
                        "client_id": client_id
                    }
                )
            )
    
    async def _handle_request(self, client_id: str, data: Dict[str, Any]):
        """Handle standard request"""
        # This would be implemented to handle non-streaming requests
        # For now, we'll just acknowledge
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    "request_id": data.get("request_id"),
                    "status": "received"
                }
            )
        )
    
    async def _handle_stream_request(self, client_id: str, data: Dict[str, Any]):
        """Handle streaming request"""
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        # Create a simple generator for testing
        async def test_generator():
            for i in range(5):
                await asyncio.sleep(0.5)
                yield f"Chunk {i+1} of response"
        
        # Start streaming
        await self.stream_response(client_id, request_id, test_generator())
    
    async def _handle_subscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        topic = data.get("topic")
        if not topic:
            await self._send_error(client_id, "Topic required for subscription")
            return
        
        self._subscribe(client_id, topic)
        
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    "action": "subscribed",
                    "topic": topic
                }
            )
        )
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        topic = data.get("topic")
        if not topic:
            await self._send_error(client_id, "Topic required for unsubscription")
            return
        
        self._unsubscribe(client_id, topic)
        
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.RESPONSE,
                data={
                    "action": "unsubscribed",
                    "topic": topic
                }
            )
        )
    
    async def _handle_ping(self, client_id: str, data: Dict[str, Any]):
        """Handle ping message"""
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.PONG,
                data={"timestamp": datetime.now().isoformat()}
            )
        )
    
    # Helper methods
    def _subscribe(self, client_id: str, topic: str):
        """Subscribe client to a topic"""
        if client_id in self.connections:
            self.connections[client_id].add_subscription(topic)
            
            if topic not in self.event_subscribers:
                self.event_subscribers[topic] = set()
            self.event_subscribers[topic].add(client_id)
            
            logger.debug(f"Client {client_id} subscribed to {topic}")
    
    def _unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe client from a topic"""
        if client_id in self.connections:
            self.connections[client_id].remove_subscription(topic)
        
        if topic in self.event_subscribers:
            self.event_subscribers[topic].discard(client_id)
            if not self.event_subscribers[topic]:
                del self.event_subscribers[topic]
        
        logger.debug(f"Client {client_id} unsubscribed from {topic}")
    
    async def _send_error(self, client_id: str, error_message: str):
        """Send error message to client"""
        await self.send_message(
            client_id,
            WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": error_message}
            )
        )
    
    def _get_capabilities(self) -> List[str]:
        """Get server capabilities"""
        return [
            "streaming",
            "events",
            "subscriptions",
            "batching",
            "compression"
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "active_subscriptions": sum(len(s.subscriptions) for s in self.connections.values()),
            "active_streams": sum(len(s.active_streams) for s in self.connections.values())
        }
    
    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """Clean up inactive connections"""
        now = datetime.now()
        inactive_clients = []
        
        for client_id, state in self.connections.items():
            inactive_time = (now - state.last_activity).total_seconds()
            if inactive_time > timeout_seconds:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            logger.info(f"Cleaning up inactive connection: {client_id}")
            await self.handle_disconnect(client_id)
        
        return len(inactive_clients)

# Global WebSocket handler instance
ws_handler = WebSocketHandler()

# Periodic cleanup task
async def periodic_cleanup():
    """Periodically clean up inactive connections"""
    while True:
        await asyncio.sleep(60)  # Check every minute
        cleaned = await ws_handler.cleanup_inactive_connections()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} inactive connections")