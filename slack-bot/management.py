"""
Workspace Installation and Channel Subscription Management
Handles bot installation, channel management, and subscription settings
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

from .oauth import (
    oauth_manager, config_manager, get_oauth_manager, get_config_manager,
    get_team_installation, BotInstallation, SlackOAuthManager, BotConfigurationManager
)
from .notifications import notification_service, NotificationType

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class ChannelSubscriptionRequest(BaseModel):
    channel_id: str = Field(..., description="Slack channel ID")
    notification_types: List[str] = Field(..., description="List of notification types to subscribe to")

class UserPreferencesRequest(BaseModel):
    dm_notifications: Optional[bool] = Field(None, description="Receive DM notifications")
    mention_notifications: Optional[bool] = Field(None, description="Receive mention notifications")
    preferred_agents: Optional[List[str]] = Field(None, description="Preferred agents for assistance")
    notification_schedule: Optional[Dict[str, Any]] = Field(None, description="Notification schedule settings")

class TeamConfigRequest(BaseModel):
    enabled_features: Optional[List[str]] = Field(None, description="Enabled bot features")
    channel_subscriptions: Optional[Dict[str, List[str]]] = Field(None, description="Channel subscription mappings")
    agent_settings: Optional[Dict[str, Any]] = Field(None, description="Agent configuration settings")

# Create router for management endpoints
router = APIRouter(prefix="/api/v1/management", tags=["management"])

@router.get("/oauth/install")
async def get_install_url(team_id: Optional[str] = None, oauth_mgr: SlackOAuthManager = Depends(get_oauth_manager)):
    """Get OAuth installation URL"""
    try:
        auth_url = oauth_mgr.get_authorization_url(team_id)
        return {
            "install_url": auth_url,
            "team_id": team_id,
            "scopes": {
                "bot": oauth_mgr.bot_scopes,
                "user": oauth_mgr.user_scopes
            }
        }
    except Exception as e:
        logger.error(f"Error generating install URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate installation URL")

@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, oauth_mgr: SlackOAuthManager = Depends(get_oauth_manager)):
    """Handle OAuth callback"""
    try:
        installation = await oauth_mgr.handle_oauth_callback(code, state)
        
        # Initialize notification service for this team
        slack_client = AsyncWebClient(token=installation.bot_token)
        if not notification_service.manager:
            await notification_service.initialize(slack_client)
        
        # Send welcome message
        await _send_welcome_message(installation, slack_client)
        
        return {
            "status": "success",
            "team_id": installation.team_id,
            "team_name": installation.team_name,
            "bot_user_id": installation.bot_user_id,
            "installed_at": installation.installed_at.isoformat(),
            "message": "Gemini Enterprise Architect bot installed successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Installation failed")

@router.delete("/oauth/uninstall/{team_id}")
async def uninstall_bot(team_id: str, oauth_mgr: SlackOAuthManager = Depends(get_oauth_manager)):
    """Uninstall bot from workspace"""
    try:
        success = await oauth_mgr.uninstall(team_id)
        if success:
            return {"status": "success", "message": "Bot uninstalled successfully"}
        else:
            raise HTTPException(status_code=404, detail="Installation not found")
    except Exception as e:
        logger.error(f"Uninstall error: {e}")
        raise HTTPException(status_code=500, detail="Failed to uninstall bot")

@router.get("/teams")
async def list_teams(oauth_mgr: SlackOAuthManager = Depends(get_oauth_manager)):
    """List all installed teams"""
    try:
        installations = oauth_mgr.list_installations()
        return {
            "teams": [
                {
                    "team_id": inst.team_id,
                    "team_name": inst.team_name,
                    "installed_at": inst.installed_at.isoformat(),
                    "enabled_features": inst.enabled_features,
                    "channel_count": len(inst.channel_subscriptions)
                }
                for inst in installations
            ],
            "total_count": len(installations)
        }
    except Exception as e:
        logger.error(f"Error listing teams: {e}")
        raise HTTPException(status_code=500, detail="Failed to list teams")

@router.get("/teams/{team_id}")
async def get_team_info(team_id: str, config_mgr: BotConfigurationManager = Depends(get_config_manager)):
    """Get detailed team information"""
    try:
        config = await config_mgr.get_team_config(team_id)
        installation = oauth_mgr.get_installation(team_id)
        
        if not installation:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get channel information
        slack_client = AsyncWebClient(token=installation.bot_token)
        channels_info = await _get_channels_info(slack_client, installation.channel_subscriptions)
        
        return {
            **config,
            "bot_user_id": installation.bot_user_id,
            "installed_at": installation.installed_at.isoformat(),
            "channels": channels_info,
            "user_count": len(installation.user_preferences)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team information")

@router.put("/teams/{team_id}/config")
async def update_team_config(
    team_id: str, 
    config_request: TeamConfigRequest,
    config_mgr: BotConfigurationManager = Depends(get_config_manager)
):
    """Update team configuration"""
    try:
        config_data = config_request.dict(exclude_unset=True)
        updated_config = await config_mgr.update_team_config(team_id, config_data)
        
        logger.info(f"Updated config for team {team_id}")
        return {"status": "success", "config": updated_config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update team configuration")

@router.get("/teams/{team_id}/channels")
async def list_team_channels(
    team_id: str,
    installation: BotInstallation = Depends(get_team_installation)
):
    """List all channels in the team with subscription status"""
    try:
        slack_client = AsyncWebClient(token=installation.bot_token)
        
        # Get all channels the bot has access to
        channels_response = await slack_client.conversations_list(types="public_channel,private_channel")
        
        if not channels_response["ok"]:
            raise HTTPException(status_code=400, detail="Failed to fetch channels")
        
        channels = []
        for channel in channels_response["channels"]:
            channel_id = channel["id"]
            subscriptions = installation.channel_subscriptions.get(channel_id, [])
            
            channels.append({
                "id": channel_id,
                "name": channel["name"],
                "is_private": channel["is_private"],
                "is_member": channel.get("is_member", False),
                "subscriptions": subscriptions,
                "subscription_count": len(subscriptions)
            })
        
        return {
            "channels": sorted(channels, key=lambda x: x["name"]),
            "total_count": len(channels),
            "subscribed_count": len([c for c in channels if c["subscriptions"]])
        }
        
    except HTTPException:
        raise
    except SlackApiError as e:
        logger.error(f"Slack API error: {e}")
        raise HTTPException(status_code=400, detail=f"Slack API error: {e}")
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to list channels")

@router.post("/teams/{team_id}/channels/subscribe")
async def subscribe_channel(
    team_id: str,
    subscription_request: ChannelSubscriptionRequest,
    config_mgr: BotConfigurationManager = Depends(get_config_manager),
    installation: BotInstallation = Depends(get_team_installation)
):
    """Subscribe a channel to notification types"""
    try:
        # Validate notification types
        valid_types = [nt.value for nt in NotificationType]
        invalid_types = [nt for nt in subscription_request.notification_types if nt not in valid_types]
        
        if invalid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid notification types: {invalid_types}. Valid types: {valid_types}"
            )
        
        # Verify channel exists and bot has access
        slack_client = AsyncWebClient(token=installation.bot_token)
        try:
            channel_info = await slack_client.conversations_info(channel=subscription_request.channel_id)
            if not channel_info["ok"]:
                raise HTTPException(status_code=404, detail="Channel not found or bot lacks access")
        except SlackApiError:
            raise HTTPException(status_code=404, detail="Channel not found or bot lacks access")
        
        # Subscribe channel
        success = await config_mgr.subscribe_channel(
            team_id, 
            subscription_request.channel_id, 
            subscription_request.notification_types
        )
        
        if success:
            # Send confirmation message to channel
            await slack_client.chat_postMessage(
                channel=subscription_request.channel_id,
                text=f"✅ Channel subscribed to: {', '.join(subscription_request.notification_types)}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ This channel is now subscribed to receive:\n• {chr(10).join(f'`{nt}`' for nt in subscription_request.notification_types)}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "Use `/gemini-ask help` to see available commands or unsubscribe anytime with the management API."
                            }
                        ]
                    }
                ]
            )
            
            return {
                "status": "success",
                "channel_id": subscription_request.channel_id,
                "subscriptions": subscription_request.notification_types,
                "message": "Channel subscribed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to subscribe channel")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe channel")

@router.delete("/teams/{team_id}/channels/{channel_id}/subscribe")
async def unsubscribe_channel(
    team_id: str,
    channel_id: str,
    config_mgr: BotConfigurationManager = Depends(get_config_manager),
    installation: BotInstallation = Depends(get_team_installation)
):
    """Unsubscribe a channel from all notifications"""
    try:
        success = await config_mgr.unsubscribe_channel(team_id, channel_id)
        
        if success:
            # Send confirmation message to channel
            slack_client = AsyncWebClient(token=installation.bot_token)
            try:
                await slack_client.chat_postMessage(
                    channel=channel_id,
                    text="🔕 Channel unsubscribed from all notifications",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "🔕 This channel has been unsubscribed from all Gemini notifications."
                            }
                        }
                    ]
                )
            except SlackApiError:
                pass  # Channel might not exist or bot might not have access
            
            return {
                "status": "success",
                "channel_id": channel_id,
                "message": "Channel unsubscribed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Channel subscription not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe channel")

@router.get("/teams/{team_id}/users/{user_id}/preferences")
async def get_user_preferences(
    team_id: str,
    user_id: str,
    config_mgr: BotConfigurationManager = Depends(get_config_manager)
):
    """Get user preferences"""
    try:
        preferences = await config_mgr.get_user_preferences(team_id, user_id)
        return {"user_id": user_id, "preferences": preferences}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user preferences")

@router.put("/teams/{team_id}/users/{user_id}/preferences")
async def update_user_preferences(
    team_id: str,
    user_id: str,
    preferences_request: UserPreferencesRequest,
    config_mgr: BotConfigurationManager = Depends(get_config_manager)
):
    """Update user preferences"""
    try:
        preferences_data = preferences_request.dict(exclude_unset=True)
        updated_preferences = await config_mgr.update_user_preferences(team_id, user_id, preferences_data)
        
        return {
            "status": "success",
            "user_id": user_id,
            "preferences": updated_preferences
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user preferences")

@router.get("/notification-types")
async def list_notification_types():
    """List all available notification types"""
    return {
        "notification_types": [
            {
                "type": nt.value,
                "name": nt.value.replace("_", " ").title(),
                "description": _get_notification_description(nt)
            }
            for nt in NotificationType
        ]
    }

@router.get("/teams/{team_id}/stats")
async def get_team_stats(
    team_id: str,
    installation: BotInstallation = Depends(get_team_installation)
):
    """Get team usage statistics"""
    try:
        # This would typically come from a metrics database
        # For now, returning mock data based on installation
        
        stats = {
            "team_id": team_id,
            "installation_date": installation.installed_at.isoformat(),
            "active_channels": len(installation.channel_subscriptions),
            "active_users": len(installation.user_preferences),
            "enabled_features": len(installation.enabled_features),
            "usage_metrics": {
                "total_commands": 0,  # Would track actual usage
                "popular_agents": ["analyst", "architect", "qa"],
                "notification_count": 0,
                "last_activity": datetime.now().isoformat()
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting team stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team statistics")

# Helper functions
async def _send_welcome_message(installation: BotInstallation, slack_client: AsyncWebClient):
    """Send welcome message after installation"""
    try:
        welcome_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 Welcome to Gemini Enterprise Architect!"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Thanks for installing the Gemini Enterprise Architect bot! I'm here to help your team with AI-powered code analysis, architecture guidance, and development assistance."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔧 Available Commands:*\n• `/gemini-analyze` - Analyze code or files\n• `/gemini-review` - Review pull requests\n• `/gemini-ask` - Ask any development question\n• `/gemini-scout` - Find duplicates and patterns\n• `/gemini-architect` - Get architecture advice\n• `/gemini-killer-demo` - Run scaling analysis"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔔 Notification Features:*\n• Guardian validation alerts\n• Scout duplicate detection\n• Build status notifications\n• Performance monitoring\n• Security vulnerability alerts"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Setup Notifications"},
                        "url": f"https://your-app.com/setup?team={installation.team_id}",
                        "action_id": "setup_notifications"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Documentation"},
                        "url": "https://your-docs.com/slack-bot",
                        "action_id": "view_docs"
                    }
                ]
            }
        ]
        
        # Send to the installing user
        await slack_client.chat_postMessage(
            channel=installation.user_id,
            text="Welcome to Gemini Enterprise Architect!",
            blocks=welcome_blocks
        )
        
    except SlackApiError as e:
        logger.warning(f"Could not send welcome message: {e}")

async def _get_channels_info(slack_client: AsyncWebClient, subscribed_channels: Dict[str, List[str]]) -> List[Dict]:
    """Get information about subscribed channels"""
    channels_info = []
    
    for channel_id, subscriptions in subscribed_channels.items():
        try:
            channel_response = await slack_client.conversations_info(channel=channel_id)
            if channel_response["ok"]:
                channel = channel_response["channel"]
                channels_info.append({
                    "id": channel_id,
                    "name": channel["name"],
                    "is_private": channel.get("is_private", False),
                    "subscriptions": subscriptions,
                    "member_count": channel.get("num_members", 0)
                })
        except SlackApiError:
            # Channel might be deleted or bot lost access
            continue
    
    return channels_info

def _get_notification_description(notification_type: NotificationType) -> str:
    """Get description for notification type"""
    descriptions = {
        NotificationType.GUARDIAN_ALERT: "Code validation and quality alerts from Guardian pipeline",
        NotificationType.SCOUT_DUPLICATE: "Duplicate code detection and similarity analysis from Scout",
        NotificationType.KILLER_DEMO_CRITICAL: "Critical scaling issues detected in killer demo analysis",
        NotificationType.BUILD_STATUS: "CI/CD build status and deployment notifications",
        NotificationType.PERFORMANCE_DEGRADATION: "Performance monitoring alerts and degradation warnings",
        NotificationType.SECURITY_VULNERABILITY: "Security vulnerability detection and alerts"
    }
    return descriptions.get(notification_type, "Notification type description not available")