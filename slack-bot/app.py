"""
Slack Bot Application for Gemini Enterprise Architect
Provides AI agent capabilities directly in Slack through slash commands and interactive components
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class SlackConfig:
    """Slack bot configuration"""
    bot_token: str
    signing_secret: str
    client_id: str
    client_secret: str
    agent_server_url: str = "http://localhost:8000"
    notification_channels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = {
                'guardian': '#alerts',
                'scout': '#code-quality',
                'killer_demo': '#critical-issues',
                'builds': '#builds'
            }

# Load configuration from environment
config = SlackConfig(
    bot_token=os.environ.get("SLACK_BOT_TOKEN", ""),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
    client_id=os.environ.get("SLACK_CLIENT_ID", ""),
    client_secret=os.environ.get("SLACK_CLIENT_SECRET", ""),
    agent_server_url=os.environ.get("AGENT_SERVER_URL", "http://localhost:8000")
)

# Initialize Slack app
slack_app = AsyncApp(
    token=config.bot_token,
    signing_secret=config.signing_secret,
    process_before_response=True
)

# FastAPI app
app = FastAPI(
    title="Gemini Slack Bot",
    description="AI Agent integration for Slack",
    version="1.0.0"
)

# Create Slack request handler
handler = AsyncSlackRequestHandler(slack_app)

class AgentClient:
    """Client for communicating with the agent server"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_agent(self, agent_type: str, action: str, payload: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an agent through the API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        request_data = {
            "type": agent_type,
            "action": action,
            "payload": payload,
            "context": context or {},
            "timeout": 30
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/agent/request",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=35)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Agent API error {response.status}: {error_text}")
        
        except asyncio.TimeoutError:
            raise Exception("Agent request timed out")
        except Exception as e:
            logger.error(f"Error calling agent {agent_type}: {e}")
            raise
    
    async def get_health(self) -> Dict[str, Any]:
        """Check agent server health"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

# Global agent client
agent_client = AgentClient(config.agent_server_url)

class SlackMessageFormatter:
    """Format agent responses for Slack"""
    
    @staticmethod
    def format_code_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
        """Format code analysis results"""
        analysis = result.get('result', {})
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Code Analysis Results"}
            },
            {
                "type": "divider"
            }
        ]
        
        # Summary section
        if 'summary' in analysis:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{analysis['summary']}"
                }
            })
        
        # Issues section
        if 'issues' in analysis and analysis['issues']:
            issues_text = "\n".join([f"• {issue}" for issue in analysis['issues'][:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issues Found:*\n{issues_text}"
                }
            })
        
        # Recommendations
        if 'recommendations' in analysis and analysis['recommendations']:
            rec_text = "\n".join([f"• {rec}" for rec in analysis['recommendations'][:3]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommendations:*\n{rec_text}"
                }
            })
        
        # Scout results if available
        scout_results = result.get('metadata', {}).get('scout_results', {})
        if scout_results.get('duplicates_found'):
            duplicates = scout_results['duplicates_found'][:3]
            dup_text = "\n".join([
                f"• `{d['function_name']}` in {d['original_file']} (similarity: {d['similarity']:.0%})"
                for d in duplicates
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Potential Duplicates:*\n{dup_text}"
                }
            })
        
        return {"blocks": blocks}
    
    @staticmethod
    def format_pr_review(result: Dict[str, Any]) -> Dict[str, Any]:
        """Format PR review results"""
        review = result.get('result', {})
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "Pull Request Review"}
            },
            {
                "type": "divider"
            }
        ]
        
        # Overall assessment
        if 'overall_score' in review:
            score = review['overall_score']
            emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *Overall Score:* {score}/10"
                }
            })
        
        # Key findings
        if 'key_findings' in review:
            findings_text = "\n".join([f"• {finding}" for finding in review['key_findings'][:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Findings:*\n{findings_text}"
                }
            })
        
        # Action items
        if 'action_items' in review and review['action_items']:
            actions_text = "\n".join([f"• {action}" for action in review['action_items'][:3]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Items:*\n{actions_text}"
                }
            })
        
        return {"blocks": blocks}
    
    @staticmethod
    def format_agent_response(agent_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format generic agent response"""
        response_data = result.get('result', {})
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{agent_type.capitalize()} Agent Response"}
            },
            {
                "type": "divider"
            }
        ]
        
        # Main content
        if isinstance(response_data, str):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": response_data[:3000]  # Slack block text limit
                }
            })
        elif isinstance(response_data, dict):
            # Format structured response
            for key, value in response_data.items():
                if isinstance(value, (str, int, float)):
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{key.replace('_', ' ').title()}:*\n{value}"
                        }
                    })
        
        return {"blocks": blocks}
    
    @staticmethod
    def format_error(error_message: str, agent_type: str = None) -> Dict[str, Any]:
        """Format error message"""
        return {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"❌ *Error{f' ({agent_type})' if agent_type else ''}:*\n{error_message}"
                    }
                }
            ]
        }

# Initialize formatter
formatter = SlackMessageFormatter()

# Add FastAPI routes for Slack
@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events"""
    return await handler.handle(request)

@app.get("/slack/oauth")
async def slack_oauth():
    """Handle OAuth installation"""
    # This would be implemented for workspace installation
    return {"message": "OAuth flow would be implemented here"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Gemini Slack Bot",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_health = await agent_client.get_health()
    return {
        "status": "healthy",
        "agent_server": agent_health.get("status", "unknown"),
        "timestamp": datetime.now().isoformat()
    }

# Store active operations for follow-up actions
active_operations: Dict[str, Dict[str, Any]] = {}

def store_operation(user_id: str, operation_type: str, data: Dict[str, Any]):
    """Store operation data for follow-up actions"""
    active_operations[f"{user_id}_{operation_type}"] = {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "type": operation_type
    }

def get_operation(user_id: str, operation_type: str) -> Optional[Dict[str, Any]]:
    """Get stored operation data"""
    key = f"{user_id}_{operation_type}"
    return active_operations.get(key)

async def send_notification(channel: str, message: str, blocks: List[Dict] = None):
    """Send notification to a Slack channel"""
    try:
        client = AsyncWebClient(token=config.bot_token)
        await client.chat_postMessage(
            channel=channel,
            text=message,
            blocks=blocks
        )
        logger.info(f"Notification sent to {channel}")
    except SlackApiError as e:
        logger.error(f"Error sending notification to {channel}: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # Start the agent client session
    async def startup():
        await agent_client.__aenter__()
    
    async def shutdown():
        await agent_client.__aexit__(None, None, None)
    
    app.add_event_handler("startup", startup)
    app.add_event_handler("shutdown", shutdown)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )