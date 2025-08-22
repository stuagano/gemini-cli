"""
Gemini Enterprise Architect Slack Bot

A comprehensive Slack bot integration that brings AI agent capabilities
directly into team communication workflows.
"""

__version__ = "1.0.0"
__author__ = "Gemini Enterprise Architect Team"
__description__ = "AI Agent integration for Slack workspaces"

# Export main components
from .app import SlackConfig, AgentClient, SlackMessageFormatter
from .commands import register_commands
from .interactive import register_interactive_components
from .notifications import NotificationService, NotificationMessage, NotificationType
from .oauth import SlackOAuthManager, BotConfigurationManager, BotInstallation
from .management import router as management_router
from .middleware import RateLimitMiddleware, ErrorHandlingMiddleware, RateLimitConfig

__all__ = [
    "SlackConfig",
    "AgentClient", 
    "SlackMessageFormatter",
    "register_commands",
    "register_interactive_components",
    "NotificationService",
    "NotificationMessage", 
    "NotificationType",
    "SlackOAuthManager",
    "BotConfigurationManager",
    "BotInstallation",
    "management_router",
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware", 
    "RateLimitConfig"
]