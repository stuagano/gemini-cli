"""
Notification System for Gemini Enterprise Architect Slack Bot
Handles real-time alerts from Guardian validation, Scout findings, and build notifications
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import aiohttp

from .app import config

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    GUARDIAN_ALERT = "guardian_alert"
    SCOUT_DUPLICATE = "scout_duplicate"
    KILLER_DEMO_CRITICAL = "killer_demo_critical"
    BUILD_STATUS = "build_status"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_VULNERABILITY = "security_vulnerability"

@dataclass
class NotificationConfig:
    """Configuration for notification channels and preferences"""
    channel_mappings: Dict[str, str]  # notification_type -> channel
    severity_channels: Dict[str, str]  # severity -> channel
    user_preferences: Dict[str, Dict[str, Any]]  # user_id -> preferences
    rate_limits: Dict[str, Dict[str, int]]  # notification_type -> rate limit config
    enabled_notifications: Set[str]
    
    @classmethod
    def default(cls):
        return cls(
            channel_mappings={
                "guardian_alert": "#alerts",
                "scout_duplicate": "#code-quality",
                "killer_demo_critical": "#critical-issues",
                "build_status": "#builds",
                "performance_degradation": "#performance",
                "security_vulnerability": "#security"
            },
            severity_channels={
                "critical": "#critical-alerts",
                "high": "#alerts",
                "medium": "#notifications",
                "low": "#updates"
            },
            user_preferences={},
            rate_limits={
                "guardian_alert": {"max_per_hour": 10, "burst": 3},
                "scout_duplicate": {"max_per_hour": 5, "burst": 2},
                "killer_demo_critical": {"max_per_hour": 2, "burst": 1},
                "build_status": {"max_per_hour": 20, "burst": 5}
            },
            enabled_notifications={
                "guardian_alert", "scout_duplicate", "killer_demo_critical",
                "build_status", "performance_degradation", "security_vulnerability"
            }
        )

@dataclass
class NotificationMessage:
    """Notification message structure"""
    id: str
    notification_type: NotificationType
    severity: str  # critical, high, medium, low
    title: str
    message: str
    details: Dict[str, Any]
    source: str
    timestamp: datetime
    channels: List[str]
    users: List[str] = None
    blocks: List[Dict] = None
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['notification_type'] = self.notification_type.value
        return data

class RateLimiter:
    """Rate limiting for notifications"""
    
    def __init__(self):
        self.counters: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, key: str, max_per_hour: int, burst: int) -> bool:
        """Check if notification is allowed based on rate limits"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        if key in self.counters:
            self.counters[key] = [ts for ts in self.counters[key] if ts > hour_ago]
        else:
            self.counters[key] = []
        
        # Check burst limit (last 5 minutes)
        five_min_ago = now - timedelta(minutes=5)
        recent_count = sum(1 for ts in self.counters[key] if ts > five_min_ago)
        
        if recent_count >= burst:
            return False
        
        # Check hourly limit
        if len(self.counters[key]) >= max_per_hour:
            return False
        
        # Allow and record
        self.counters[key].append(now)
        return True

class NotificationManager:
    """Manages all notification handling"""
    
    def __init__(self, slack_client: AsyncWebClient):
        self.slack_client = slack_client
        self.config = NotificationConfig.default()
        self.rate_limiter = RateLimiter()
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> user_ids
        self.webhook_handlers = {}
        
    async def initialize(self):
        """Initialize notification manager"""
        await self._load_user_preferences()
        await self._setup_webhook_handlers()
        logger.info("Notification manager initialized")
    
    async def send_notification(self, notification: NotificationMessage) -> bool:
        """Send a notification message"""
        # Check if notification type is enabled
        if notification.notification_type.value not in self.config.enabled_notifications:
            logger.debug(f"Notification type {notification.notification_type.value} is disabled")
            return False
        
        # Check rate limits
        rate_limit_key = f"{notification.notification_type.value}_{notification.severity}"
        rate_config = self.config.rate_limits.get(notification.notification_type.value, {})
        
        if not self.rate_limiter.is_allowed(
            rate_limit_key,
            rate_config.get('max_per_hour', 10),
            rate_config.get('burst', 3)
        ):
            logger.warning(f"Rate limit exceeded for {rate_limit_key}")
            return False
        
        # Determine target channels
        channels = self._get_target_channels(notification)
        
        # Format message blocks
        blocks = notification.blocks or self._format_notification_blocks(notification)
        
        # Send to each channel
        sent_successfully = True
        for channel in channels:
            try:
                await self.slack_client.chat_postMessage(
                    channel=channel,
                    text=notification.title,  # Fallback text
                    blocks=blocks
                )
                logger.info(f"Notification sent to {channel}: {notification.title}")
            except SlackApiError as e:
                logger.error(f"Failed to send notification to {channel}: {e}")
                sent_successfully = False
        
        # Send direct messages to specific users if specified
        if notification.users:
            for user_id in notification.users:
                try:
                    await self.slack_client.chat_postMessage(
                        channel=user_id,
                        text=notification.title,
                        blocks=blocks
                    )
                except SlackApiError as e:
                    logger.error(f"Failed to send DM to {user_id}: {e}")
        
        return sent_successfully
    
    def _get_target_channels(self, notification: NotificationMessage) -> List[str]:
        """Determine target channels for notification"""
        channels = []
        
        # Add default channel for notification type
        default_channel = self.config.channel_mappings.get(notification.notification_type.value)
        if default_channel:
            channels.append(default_channel)
        
        # Add severity-based channel
        severity_channel = self.config.severity_channels.get(notification.severity)
        if severity_channel and severity_channel not in channels:
            channels.append(severity_channel)
        
        # Add explicitly specified channels
        if notification.channels:
            for channel in notification.channels:
                if channel not in channels:
                    channels.append(channel)
        
        return channels
    
    def _format_notification_blocks(self, notification: NotificationMessage) -> List[Dict]:
        """Format notification into Slack blocks"""
        severity_emojis = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "ℹ️",
            "low": "💬"
        }
        
        emoji = severity_emojis.get(notification.severity, "📢")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {notification.title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": notification.message
                }
            }
        ]
        
        # Add context information
        context_elements = [
            {
                "type": "mrkdwn",
                "text": f"*Source:* {notification.source}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Severity:* {notification.severity}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Time:* {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
        
        blocks.append({
            "type": "context",
            "elements": context_elements
        })
        
        # Add details if available
        if notification.details:
            details_text = self._format_details(notification.details)
            if details_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:*\n{details_text}"
                    }
                })
        
        # Add divider
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary into readable text"""
        formatted_lines = []
        for key, value in details.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value[:3])
                if len(value) > 3:
                    value_str += f" (and {len(value) - 3} more)"
            else:
                value_str = str(value)
            
            formatted_lines.append(f"• {key.replace('_', ' ').title()}: {value_str}")
        
        return "\n".join(formatted_lines[:5])  # Limit to 5 lines
    
    async def _load_user_preferences(self):
        """Load user notification preferences"""
        # This would typically load from a database or config file
        # For now, using default settings
        pass
    
    async def _setup_webhook_handlers(self):
        """Setup webhook handlers for external systems"""
        # Guardian webhook handler
        self.webhook_handlers['guardian'] = self._handle_guardian_webhook
        
        # Scout webhook handler
        self.webhook_handlers['scout'] = self._handle_scout_webhook
        
        # Build system webhook handler
        self.webhook_handlers['builds'] = self._handle_build_webhook
    
    async def _handle_guardian_webhook(self, payload: Dict[str, Any]) -> NotificationMessage:
        """Handle Guardian validation webhook"""
        validation_result = payload.get('validation_result', {})
        severity = "critical" if validation_result.get('critical_issues') else "high"
        
        details = {
            'validation_id': payload.get('validation_id'),
            'file_path': payload.get('file_path'),
            'issues_found': len(validation_result.get('issues', [])),
            'critical_issues': len(validation_result.get('critical_issues', [])),
            'recommendations': validation_result.get('recommendations', [])[:3]
        }
        
        return NotificationMessage(
            id=f"guardian_{payload.get('validation_id', 'unknown')}",
            notification_type=NotificationType.GUARDIAN_ALERT,
            severity=severity,
            title="Guardian Validation Alert",
            message=f"Guardian detected {details['issues_found']} issues in {details['file_path']}",
            details=details,
            source="Guardian Validation Pipeline",
            timestamp=datetime.now(),
            channels=[]
        )
    
    async def _handle_scout_webhook(self, payload: Dict[str, Any]) -> NotificationMessage:
        """Handle Scout duplicate detection webhook"""
        duplicates = payload.get('duplicates', [])
        severity = "medium" if len(duplicates) > 5 else "low"
        
        details = {
            'scan_id': payload.get('scan_id'),
            'total_duplicates': len(duplicates),
            'files_affected': len(set(d.get('file') for d in duplicates)),
            'top_duplicates': [d.get('function_name') for d in duplicates[:3]],
            'similarity_threshold': payload.get('similarity_threshold', 0.8)
        }
        
        return NotificationMessage(
            id=f"scout_{payload.get('scan_id', 'unknown')}",
            notification_type=NotificationType.SCOUT_DUPLICATE,
            severity=severity,
            title="Scout Duplicate Detection",
            message=f"Scout found {len(duplicates)} potential duplicates affecting {details['files_affected']} files",
            details=details,
            source="Scout Code Analysis",
            timestamp=datetime.now(),
            channels=[]
        )
    
    async def _handle_build_webhook(self, payload: Dict[str, Any]) -> NotificationMessage:
        """Handle build system webhook"""
        build_status = payload.get('status', 'unknown')
        severity = "high" if build_status == 'failed' else "low"
        
        details = {
            'build_id': payload.get('build_id'),
            'project': payload.get('project'),
            'branch': payload.get('branch'),
            'commit': payload.get('commit', '')[:8],
            'duration': payload.get('duration'),
            'tests_passed': payload.get('tests_passed'),
            'tests_failed': payload.get('tests_failed')
        }
        
        status_emoji = "✅" if build_status == 'success' else "❌" if build_status == 'failed' else "⏳"
        
        return NotificationMessage(
            id=f"build_{payload.get('build_id', 'unknown')}",
            notification_type=NotificationType.BUILD_STATUS,
            severity=severity,
            title=f"Build {build_status.title()}",
            message=f"{status_emoji} Build {build_status} for {details['project']} on {details['branch']}",
            details=details,
            source="CI/CD Pipeline",
            timestamp=datetime.now(),
            channels=[]
        )

class NotificationService:
    """Main notification service interface"""
    
    def __init__(self):
        self.manager: Optional[NotificationManager] = None
        self.webhook_server_running = False
    
    async def initialize(self, slack_client: AsyncWebClient):
        """Initialize the notification service"""
        self.manager = NotificationManager(slack_client)
        await self.manager.initialize()
        
    async def start_webhook_server(self, port: int = 3001):
        """Start webhook server for external integrations"""
        from aiohttp import web
        
        app = web.Application()
        
        # Webhook endpoints
        app.router.add_post('/webhooks/guardian', self._guardian_webhook_handler)
        app.router.add_post('/webhooks/scout', self._scout_webhook_handler)
        app.router.add_post('/webhooks/builds', self._build_webhook_handler)
        app.router.add_post('/webhooks/killer-demo', self._killer_demo_webhook_handler)
        
        # Health check
        app.router.add_get('/health', self._health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        self.webhook_server_running = True
        logger.info(f"Webhook server started on port {port}")
    
    async def _guardian_webhook_handler(self, request):
        """Handle Guardian webhook requests"""
        try:
            payload = await request.json()
            notification = await self.manager._handle_guardian_webhook(payload)
            await self.manager.send_notification(notification)
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Error handling Guardian webhook: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def _scout_webhook_handler(self, request):
        """Handle Scout webhook requests"""
        try:
            payload = await request.json()
            notification = await self.manager._handle_scout_webhook(payload)
            await self.manager.send_notification(notification)
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Error handling Scout webhook: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def _build_webhook_handler(self, request):
        """Handle build webhook requests"""
        try:
            payload = await request.json()
            notification = await self.manager._handle_build_webhook(payload)
            await self.manager.send_notification(notification)
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Error handling build webhook: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def _killer_demo_webhook_handler(self, request):
        """Handle killer demo critical issue webhook"""
        try:
            payload = await request.json()
            
            critical_issues = payload.get('critical_issues', [])
            severity = "critical" if len(critical_issues) > 0 else "high"
            
            details = {
                'analysis_id': payload.get('analysis_id'),
                'repository': payload.get('repository'),
                'critical_count': len(critical_issues),
                'scaling_score': payload.get('scaling_score', 0),
                'top_issues': [issue.get('description') for issue in critical_issues[:3]]
            }
            
            notification = NotificationMessage(
                id=f"killer_demo_{payload.get('analysis_id', 'unknown')}",
                notification_type=NotificationType.KILLER_DEMO_CRITICAL,
                severity=severity,
                title="Killer Demo Critical Issues Detected",
                message=f"🚨 Killer demo analysis found {len(critical_issues)} critical scaling issues",
                details=details,
                source="Killer Demo Analysis",
                timestamp=datetime.now(),
                channels=[]
            )
            
            await self.manager.send_notification(notification)
            return web.json_response({"status": "success"})
            
        except Exception as e:
            logger.error(f"Error handling killer demo webhook: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def _health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "service": "notification_service",
            "webhook_server": self.webhook_server_running,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_custom_notification(self, 
                                     notification_type: str,
                                     title: str, 
                                     message: str,
                                     severity: str = "medium",
                                     details: Dict[str, Any] = None,
                                     channels: List[str] = None,
                                     users: List[str] = None) -> bool:
        """Send a custom notification"""
        if not self.manager:
            logger.error("Notification manager not initialized")
            return False
        
        notification = NotificationMessage(
            id=f"custom_{datetime.now().timestamp()}",
            notification_type=NotificationType(notification_type),
            severity=severity,
            title=title,
            message=message,
            details=details or {},
            source="Slack Bot",
            timestamp=datetime.now(),
            channels=channels or [],
            users=users or []
        )
        
        return await self.manager.send_notification(notification)

# Global notification service instance
notification_service = NotificationService()