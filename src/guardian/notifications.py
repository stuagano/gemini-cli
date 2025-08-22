"""
Guardian Real-time Notification System
Provides real-time notifications for validation results and code quality alerts
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import deque
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    VALIDATION_ERROR = "validation_error"
    VALIDATION_WARNING = "validation_warning"
    VALIDATION_SUCCESS = "validation_success"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_ISSUE = "performance_issue"
    BREAKING_CHANGE = "breaking_change"
    DUPLICATE_FOUND = "duplicate_found"
    TEST_FAILURE = "test_failure"
    BUILD_FAILURE = "build_failure"
    INFO = "info"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Notification:
    """Represents a notification"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    file_path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    actions: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.actions is None:
            self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'file_path': self.file_path,
            'line': self.line,
            'column': self.column,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'actions': self.actions
        }

class NotificationChannel:
    """Base class for notification channels"""
    
    async def send(self, notification: Notification) -> bool:
        """Send notification through this channel"""
        raise NotImplementedError

class WebSocketChannel(NotificationChannel):
    """WebSocket notification channel for real-time updates"""
    
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.port = 8001
    
    async def start_server(self):
        """Start WebSocket server"""
        async def handler(websocket, path):
            self.clients.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                self.clients.remove(websocket)
        
        self.server = await websockets.serve(handler, "localhost", self.port)
        logger.info(f"WebSocket notification server started on port {self.port}")
    
    async def stop_server(self):
        """Stop WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def send(self, notification: Notification) -> bool:
        """Broadcast notification to all connected clients"""
        if not self.clients:
            return False
        
        message = json.dumps(notification.to_dict())
        
        # Send to all connected clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
        
        return len(self.clients) > 0

class ConsoleChannel(NotificationChannel):
    """Console notification channel for CLI output"""
    
    def __init__(self, formatter: Optional[Callable] = None):
        self.formatter = formatter or self._default_formatter
    
    def _default_formatter(self, notification: Notification) -> str:
        """Default console formatter"""
        icons = {
            NotificationType.VALIDATION_ERROR: "❌",
            NotificationType.VALIDATION_WARNING: "⚠️",
            NotificationType.VALIDATION_SUCCESS: "✅",
            NotificationType.SECURITY_ALERT: "🔒",
            NotificationType.PERFORMANCE_ISSUE: "🐌",
            NotificationType.BREAKING_CHANGE: "💥",
            NotificationType.DUPLICATE_FOUND: "🔍",
            NotificationType.TEST_FAILURE: "🧪",
            NotificationType.BUILD_FAILURE: "🏗️",
            NotificationType.INFO: "ℹ️"
        }
        
        icon = icons.get(notification.type, "📢")
        location = ""
        
        if notification.file_path:
            location = f" [{notification.file_path}"
            if notification.line:
                location += f":{notification.line}"
                if notification.column:
                    location += f":{notification.column}"
            location += "]"
        
        return f"{icon} {notification.title}{location}\n   {notification.message}"
    
    async def send(self, notification: Notification) -> bool:
        """Print notification to console"""
        formatted = self.formatter(notification)
        print(formatted)
        return True

class FileChannel(NotificationChannel):
    """File-based notification channel for logging"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    async def send(self, notification: Notification) -> bool:
        """Write notification to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(notification.to_dict()) + '\n')
            return True
        except Exception as e:
            logger.error(f"Failed to write notification to file: {e}")
            return False

class NotificationManager:
    """Manages notifications across multiple channels"""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.history: deque = deque(maxlen=1000)
        self.subscribers: Dict[NotificationType, List[Callable]] = {}
        self.filters: List[Callable] = []
        self.notification_id = 0
    
    def add_channel(self, channel: NotificationChannel):
        """Add a notification channel"""
        self.channels.append(channel)
    
    def remove_channel(self, channel: NotificationChannel):
        """Remove a notification channel"""
        if channel in self.channels:
            self.channels.remove(channel)
    
    def subscribe(self, notification_type: NotificationType, callback: Callable):
        """Subscribe to specific notification types"""
        if notification_type not in self.subscribers:
            self.subscribers[notification_type] = []
        self.subscribers[notification_type].append(callback)
    
    def unsubscribe(self, notification_type: NotificationType, callback: Callable):
        """Unsubscribe from notifications"""
        if notification_type in self.subscribers:
            if callback in self.subscribers[notification_type]:
                self.subscribers[notification_type].remove(callback)
    
    def add_filter(self, filter_func: Callable[[Notification], bool]):
        """Add a filter function to control which notifications are sent"""
        self.filters.append(filter_func)
    
    async def notify(self, 
                    type: NotificationType,
                    title: str,
                    message: str,
                    priority: NotificationPriority = NotificationPriority.NORMAL,
                    **kwargs) -> Notification:
        """Create and send a notification"""
        
        # Generate notification ID
        self.notification_id += 1
        notification_id = f"notif_{self.notification_id}_{datetime.now().timestamp()}"
        
        # Create notification
        notification = Notification(
            id=notification_id,
            type=type,
            priority=priority,
            title=title,
            message=message,
            **kwargs
        )
        
        # Apply filters
        for filter_func in self.filters:
            if not filter_func(notification):
                logger.debug(f"Notification {notification_id} filtered out")
                return notification
        
        # Add to history
        self.history.append(notification)
        
        # Send to channels
        for channel in self.channels:
            try:
                await channel.send(notification)
            except Exception as e:
                logger.error(f"Failed to send notification through channel {channel}: {e}")
        
        # Call subscribers
        if type in self.subscribers:
            for callback in self.subscribers[type]:
                try:
                    await callback(notification) if asyncio.iscoroutinefunction(callback) else callback(notification)
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")
        
        return notification
    
    async def notify_validation_result(self, validation_report):
        """Send notification based on validation report"""
        from .validation_pipeline import ValidationReport
        
        if validation_report.status == 'failed':
            # Find most severe issue
            critical_issues = [i for i in validation_report.issues if i.severity == 'critical']
            error_issues = [i for i in validation_report.issues if i.severity == 'error']
            
            if critical_issues:
                issue = critical_issues[0]
                await self.notify(
                    type=NotificationType.VALIDATION_ERROR,
                    priority=NotificationPriority.CRITICAL,
                    title=f"Critical validation failure in {validation_report.file_path}",
                    message=issue.message,
                    file_path=validation_report.file_path,
                    line=issue.line,
                    metadata={'total_issues': len(validation_report.issues)}
                )
            elif error_issues:
                issue = error_issues[0]
                await self.notify(
                    type=NotificationType.VALIDATION_ERROR,
                    priority=NotificationPriority.HIGH,
                    title=f"Validation errors in {validation_report.file_path}",
                    message=f"{len(error_issues)} errors found",
                    file_path=validation_report.file_path,
                    metadata={'issues': [i.message for i in error_issues[:3]]}
                )
        
        elif validation_report.status == 'warning':
            warning_issues = [i for i in validation_report.issues if i.severity == 'warning']
            await self.notify(
                type=NotificationType.VALIDATION_WARNING,
                priority=NotificationPriority.NORMAL,
                title=f"Validation warnings in {validation_report.file_path}",
                message=f"{len(warning_issues)} warnings found",
                file_path=validation_report.file_path,
                metadata={'issues': [i.message for i in warning_issues[:3]]}
            )
        
        else:
            await self.notify(
                type=NotificationType.VALIDATION_SUCCESS,
                priority=NotificationPriority.LOW,
                title=f"Validation passed for {validation_report.file_path}",
                message="All checks passed successfully",
                file_path=validation_report.file_path
            )
    
    def get_history(self, limit: int = 100, type_filter: Optional[NotificationType] = None) -> List[Notification]:
        """Get notification history"""
        history = list(self.history)
        
        if type_filter:
            history = [n for n in history if n.type == type_filter]
        
        return history[-limit:]
    
    def clear_history(self):
        """Clear notification history"""
        self.history.clear()
    
    async def close(self):
        """Clean up resources"""
        for channel in self.channels:
            if isinstance(channel, WebSocketChannel):
                await channel.stop_server()

class NotificationConfig:
    """Configuration for notification system"""
    
    def __init__(self):
        self.enable_console = True
        self.enable_websocket = True
        self.enable_file_logging = False
        self.log_file = "guardian_notifications.log"
        self.websocket_port = 8001
        self.min_priority = NotificationPriority.LOW
        self.ignored_paths = set()
        self.suppressed_types = set()
    
    def should_notify(self, notification: Notification) -> bool:
        """Check if notification should be sent based on config"""
        # Check priority
        if notification.priority.value < self.min_priority.value:
            return False
        
        # Check suppressed types
        if notification.type in self.suppressed_types:
            return False
        
        # Check ignored paths
        if notification.file_path:
            for ignored_path in self.ignored_paths:
                if ignored_path in notification.file_path:
                    return False
        
        return True

# Singleton instance
_manager_instance: Optional[NotificationManager] = None
_config_instance: Optional[NotificationConfig] = None

async def initialize_notifications(config: Optional[NotificationConfig] = None) -> NotificationManager:
    """Initialize the notification system"""
    global _manager_instance, _config_instance
    
    if _manager_instance is None:
        _manager_instance = NotificationManager()
        _config_instance = config or NotificationConfig()
        
        # Add channels based on config
        if _config_instance.enable_console:
            _manager_instance.add_channel(ConsoleChannel())
        
        if _config_instance.enable_websocket:
            ws_channel = WebSocketChannel()
            ws_channel.port = _config_instance.websocket_port
            await ws_channel.start_server()
            _manager_instance.add_channel(ws_channel)
        
        if _config_instance.enable_file_logging:
            _manager_instance.add_channel(FileChannel(_config_instance.log_file))
        
        # Add config filter
        _manager_instance.add_filter(_config_instance.should_notify)
    
    return _manager_instance

def get_notification_manager() -> Optional[NotificationManager]:
    """Get the notification manager instance"""
    return _manager_instance

def get_notification_config() -> Optional[NotificationConfig]:
    """Get the notification config"""
    return _config_instance