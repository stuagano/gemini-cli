"""
OAuth Setup and Bot Configuration for Gemini Enterprise Architect Slack Bot
Handles workspace installation, authentication, and configuration management
"""

import os
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from urllib.parse import urlencode

from fastapi import HTTPException, Request, Depends
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.state_store import OAuthStateStore
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

@dataclass
class BotInstallation:
    """Represents a bot installation in a workspace"""
    team_id: str
    team_name: str
    bot_token: str
    bot_user_id: str
    bot_scopes: List[str]
    user_id: str
    user_token: Optional[str]
    user_scopes: List[str]
    installed_at: datetime
    webhook_url: Optional[str] = None
    channel_subscriptions: Dict[str, List[str]] = None  # channel_id -> notification_types
    user_preferences: Dict[str, Dict[str, Any]] = None  # user_id -> preferences
    enabled_features: List[str] = None
    
    def __post_init__(self):
        if self.channel_subscriptions is None:
            self.channel_subscriptions = {}
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.enabled_features is None:
            self.enabled_features = [
                "slash_commands", "interactive_components", 
                "notifications", "guardian_alerts", "scout_analysis"
            ]
    
    def to_dict(self):
        data = asdict(self)
        data['installed_at'] = self.installed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data['installed_at'] = datetime.fromisoformat(data['installed_at'])
        return cls(**data)

class InMemoryInstallationStore:
    """In-memory installation store (use database in production)"""
    
    def __init__(self):
        self.installations: Dict[str, BotInstallation] = {}
    
    def save(self, installation: BotInstallation):
        """Save installation"""
        self.installations[installation.team_id] = installation
        logger.info(f"Saved installation for team {installation.team_id}")
    
    def find_by_team_id(self, team_id: str) -> Optional[BotInstallation]:
        """Find installation by team ID"""
        return self.installations.get(team_id)
    
    def find_by_user_id(self, user_id: str) -> Optional[BotInstallation]:
        """Find installation by user ID"""
        for installation in self.installations.values():
            if installation.user_id == user_id:
                return installation
        return None
    
    def delete(self, team_id: str):
        """Delete installation"""
        if team_id in self.installations:
            del self.installations[team_id]
            logger.info(f"Deleted installation for team {team_id}")
    
    def list_all(self) -> List[BotInstallation]:
        """List all installations"""
        return list(self.installations.values())

class InMemoryStateStore(OAuthStateStore):
    """In-memory OAuth state store"""
    
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
    
    def issue(self, client_id: str) -> str:
        """Issue a new state"""
        state = secrets.token_urlsafe(32)
        self.states[state] = {
            'client_id': client_id,
            'issued_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        return state
    
    def consume(self, state: str) -> bool:
        """Consume state (one-time use)"""
        if state not in self.states:
            return False
        
        state_data = self.states[state]
        if datetime.now() > state_data['expires_at']:
            del self.states[state]
            return False
        
        del self.states[state]
        return True

class SlackOAuthManager:
    """Manages Slack OAuth flow and installations"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.installation_store = InMemoryInstallationStore()
        self.state_store = InMemoryStateStore()
        
        # Required scopes for the bot
        self.bot_scopes = [
            "app_mentions:read",
            "channels:read",
            "chat:write",
            "chat:write.public",
            "commands",
            "files:read",
            "groups:read",
            "im:read",
            "im:write",
            "mpim:read",
            "reactions:read",
            "reactions:write",
            "team:read",
            "users:read",
            "users:read.email",
            "users.profile:read"
        ]
        
        # Optional user scopes
        self.user_scopes = [
            "identify",
            "users:read"
        ]
    
    def get_authorization_url(self, team_id: Optional[str] = None) -> str:
        """Generate OAuth authorization URL"""
        state = self.state_store.issue(self.client_id)
        
        params = {
            'client_id': self.client_id,
            'scope': ','.join(self.bot_scopes),
            'user_scope': ','.join(self.user_scopes),
            'redirect_uri': self.redirect_uri,
            'state': state
        }
        
        if team_id:
            params['team'] = team_id
        
        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str, state: str) -> BotInstallation:
        """Handle OAuth callback and save installation"""
        # Verify state
        if not self.state_store.consume(state):
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        # Exchange code for token
        client = AsyncWebClient()
        
        try:
            response = await client.oauth_v2_access(
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code,
                redirect_uri=self.redirect_uri
            )
            
            if not response["ok"]:
                raise HTTPException(status_code=400, detail=f"OAuth error: {response['error']}")
            
            # Extract installation data
            team = response["team"]
            bot = response.get("bot", {})
            authed_user = response.get("authed_user", {})
            
            installation = BotInstallation(
                team_id=team["id"],
                team_name=team["name"],
                bot_token=response["access_token"],
                bot_user_id=bot.get("id"),
                bot_scopes=response.get("scope", "").split(","),
                user_id=authed_user.get("id"),
                user_token=authed_user.get("access_token"),
                user_scopes=authed_user.get("scope", "").split(",") if authed_user.get("scope") else [],
                installed_at=datetime.now()
            )
            
            # Save installation
            self.installation_store.save(installation)
            
            logger.info(f"Bot installed successfully for team {team['name']} ({team['id']})")
            return installation
            
        except SlackApiError as e:
            logger.error(f"OAuth error: {e}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {e}")
    
    def get_installation(self, team_id: str) -> Optional[BotInstallation]:
        """Get installation by team ID"""
        return self.installation_store.find_by_team_id(team_id)
    
    def get_bot_token(self, team_id: str) -> Optional[str]:
        """Get bot token for team"""
        installation = self.get_installation(team_id)
        return installation.bot_token if installation else None
    
    async def uninstall(self, team_id: str) -> bool:
        """Handle bot uninstallation"""
        installation = self.get_installation(team_id)
        if not installation:
            return False
        
        # Revoke tokens if possible
        try:
            client = AsyncWebClient(token=installation.bot_token)
            await client.auth_revoke()
        except SlackApiError as e:
            logger.warning(f"Error revoking token for team {team_id}: {e}")
        
        # Remove from store
        self.installation_store.delete(team_id)
        logger.info(f"Bot uninstalled from team {team_id}")
        return True
    
    def list_installations(self) -> List[BotInstallation]:
        """List all installations"""
        return self.installation_store.list_all()

class BotConfigurationManager:
    """Manages bot configuration per workspace"""
    
    def __init__(self, oauth_manager: SlackOAuthManager):
        self.oauth_manager = oauth_manager
    
    async def get_team_config(self, team_id: str) -> Dict[str, Any]:
        """Get configuration for a team"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return {
            "team_id": team_id,
            "team_name": installation.team_name,
            "enabled_features": installation.enabled_features,
            "channel_subscriptions": installation.channel_subscriptions,
            "notification_settings": {
                "guardian_alerts": True,
                "scout_findings": True,
                "build_notifications": True,
                "killer_demo_alerts": True
            },
            "agent_settings": {
                "default_timeout": 30,
                "max_concurrent_requests": 5,
                "scout_similarity_threshold": 0.8
            }
        }
    
    async def update_team_config(self, team_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update team configuration"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Update enabled features
        if "enabled_features" in config:
            installation.enabled_features = config["enabled_features"]
        
        # Update channel subscriptions
        if "channel_subscriptions" in config:
            installation.channel_subscriptions.update(config["channel_subscriptions"])
        
        # Save updated installation
        self.oauth_manager.installation_store.save(installation)
        
        return await self.get_team_config(team_id)
    
    async def subscribe_channel(self, team_id: str, channel_id: str, notification_types: List[str]) -> bool:
        """Subscribe a channel to notification types"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            return False
        
        installation.channel_subscriptions[channel_id] = notification_types
        self.oauth_manager.installation_store.save(installation)
        
        logger.info(f"Channel {channel_id} subscribed to {notification_types} in team {team_id}")
        return True
    
    async def unsubscribe_channel(self, team_id: str, channel_id: str) -> bool:
        """Unsubscribe a channel from all notifications"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            return False
        
        if channel_id in installation.channel_subscriptions:
            del installation.channel_subscriptions[channel_id]
            self.oauth_manager.installation_store.save(installation)
            logger.info(f"Channel {channel_id} unsubscribed from notifications in team {team_id}")
        
        return True
    
    async def get_user_preferences(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return installation.user_preferences.get(user_id, {
            "dm_notifications": False,
            "mention_notifications": True,
            "preferred_agents": ["analyst", "architect"],
            "notification_schedule": {
                "start_hour": 9,
                "end_hour": 17,
                "timezone": "UTC"
            }
        })
    
    async def update_user_preferences(self, team_id: str, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        installation = self.oauth_manager.get_installation(team_id)
        if not installation:
            raise HTTPException(status_code=404, detail="Team not found")
        
        if user_id not in installation.user_preferences:
            installation.user_preferences[user_id] = {}
        
        installation.user_preferences[user_id].update(preferences)
        self.oauth_manager.installation_store.save(installation)
        
        return installation.user_preferences[user_id]

# Initialize OAuth manager with environment variables
oauth_manager = SlackOAuthManager(
    client_id=os.environ.get("SLACK_CLIENT_ID", ""),
    client_secret=os.environ.get("SLACK_CLIENT_SECRET", ""),
    redirect_uri=os.environ.get("SLACK_REDIRECT_URI", "http://localhost:3000/slack/oauth/callback")
)

# Initialize configuration manager
config_manager = BotConfigurationManager(oauth_manager)

def get_oauth_manager() -> SlackOAuthManager:
    """Dependency to get OAuth manager"""
    return oauth_manager

def get_config_manager() -> BotConfigurationManager:
    """Dependency to get configuration manager"""
    return config_manager

async def get_team_installation(team_id: str) -> BotInstallation:
    """Dependency to get team installation"""
    installation = oauth_manager.get_installation(team_id)
    if not installation:
        raise HTTPException(status_code=404, detail="Team not found or bot not installed")
    return installation

async def verify_request_signature(request: Request, signing_secret: str) -> bool:
    """Verify Slack request signature"""
    import hmac
    import hashlib
    import time
    
    # Get headers
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    
    if not timestamp or not signature:
        return False
    
    # Check timestamp (prevent replay attacks)
    if abs(time.time() - int(timestamp)) > 60 * 5:  # 5 minutes
        return False
    
    # Get request body
    body = await request.body()
    
    # Create signature
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    expected_signature = "v0=" + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)