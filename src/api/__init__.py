"""
API Module for BMAD Agent Server
Provides REST and WebSocket interfaces for agent orchestration
"""

from .agent_server import app, AgentRequest, AgentResponse, HealthStatus, SystemMetrics
from .router import AgentRouter, RoutingRule
from .websocket_handler import WebSocketHandler, WebSocketMessage, MessageType, ws_handler
from .queue_broker import QueueBroker, QueuedTask, Priority, TaskStatus, queue_broker

__all__ = [
    # FastAPI app
    'app',
    
    # Request/Response models
    'AgentRequest',
    'AgentResponse',
    'HealthStatus',
    'SystemMetrics',
    
    # Router
    'AgentRouter',
    'RoutingRule',
    
    # WebSocket
    'WebSocketHandler',
    'WebSocketMessage',
    'MessageType',
    'ws_handler',
    
    # Queue
    'QueueBroker',
    'QueuedTask',
    'Priority',
    'TaskStatus',
    'queue_broker'
]

# Version
__version__ = '1.0.0'