"""
Gemini Enterprise Architect GitHub App
Provides webhook handlers for PR events, status checks, and comment generation
"""

import os
import json
import hmac
import hashlib
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
import jwt
from cryptography.hazmat.primitives import serialization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GitHubAppConfig:
    """GitHub App configuration"""
    app_id: str
    private_key: str
    webhook_secret: str
    agent_server_url: str
    installation_id: Optional[str] = None

class GitHubAppAuth:
    """Handles GitHub App authentication"""
    
    def __init__(self, config: GitHubAppConfig):
        self.config = config
        self.private_key = serialization.load_pem_private_key(
            config.private_key.encode(), password=None
        )
    
    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = datetime.utcnow()
        payload = {
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(minutes=10)).timestamp()),
            'iss': self.config.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    async def get_installation_token(self, installation_id: str) -> str:
        """Get installation access token"""
        jwt_token = self.generate_jwt()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get installation token: {response.text}"
                )
            
            return response.json()["token"]

class WebhookHandler:
    """Handles GitHub webhook events"""
    
    def __init__(self, config: GitHubAppConfig, auth: GitHubAppAuth):
        self.config = config
        self.auth = auth
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        expected = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    async def handle_pull_request(self, payload: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Handle pull request events"""
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        
        if action not in ["opened", "synchronize", "reopened"]:
            return {"message": f"Ignored PR action: {action}"}
        
        logger.info(f"Processing PR #{pr.get('number')} - {action}")
        
        # Get installation token
        token = await self.auth.get_installation_token(installation_id)
        
        # Trigger analysis based on PR changes
        analysis_tasks = [
            self._trigger_scaling_analysis(payload, token),
            self._trigger_duplicate_detection(payload, token),
            self._trigger_code_review(payload, token)
        ]
        
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        return {
            "pr_number": pr.get("number"),
            "action": action,
            "analyses_triggered": len([r for r in results if not isinstance(r, Exception)]),
            "errors": [str(r) for r in results if isinstance(r, Exception)]
        }
    
    async def handle_push(self, payload: Dict[str, Any], installation_id: str) -> Dict[str, Any]:
        """Handle push events"""
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        
        if not ref.endswith(("main", "master", "develop")):
            return {"message": f"Ignored push to {ref}"}
        
        logger.info(f"Processing push to {ref} with {len(commits)} commits")
        
        # Get installation token
        token = await self.auth.get_installation_token(installation_id)
        
        # Trigger project-wide analysis for main branch pushes
        if len(commits) > 5:  # Large push, trigger comprehensive analysis
            await self._trigger_comprehensive_analysis(payload, token)
        
        return {
            "ref": ref,
            "commits": len(commits),
            "analysis_triggered": True
        }
    
    async def _trigger_scaling_analysis(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Trigger killer demo scaling analysis"""
        pr = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        # Get changed files
        changed_files = await self._get_pr_changed_files(
            repository.get("full_name"),
            pr.get("number"),
            token
        )
        
        # Send request to agent server
        analysis_request = {
            "id": f"scaling-pr-{pr.get('number')}-{datetime.utcnow().isoformat()}",
            "type": "developer",
            "action": "analyze_scaling",
            "payload": {
                "files": changed_files,
                "repository": repository.get("full_name"),
                "pr_number": pr.get("number"),
                "commit_sha": pr.get("head", {}).get("sha"),
                "severity_threshold": "medium"
            },
            "context": {
                "github_event": "pull_request",
                "webhook_triggered": True,
                "analysis_type": "killer_demo_scaling"
            },
            "timeout": 300
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.agent_server_url}/api/v1/agent/request",
                json=analysis_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update PR with scaling analysis results
                await self._update_pr_status(
                    repository.get("full_name"),
                    pr.get("head", {}).get("sha"),
                    "gemini/scaling-analysis",
                    result,
                    token
                )
                
                return result
            else:
                raise Exception(f"Scaling analysis failed: {response.status_code}")
    
    async def _trigger_duplicate_detection(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Trigger Scout duplicate detection"""
        pr = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        # Check for duplicates via Scout endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.agent_server_url}/api/v1/scout/duplicates",
                params={"similarity_threshold": 0.8},
                timeout=60
            )
            
            if response.status_code == 200:
                duplicates_data = response.json()
                
                # Update PR with duplicate detection results
                await self._update_pr_status(
                    repository.get("full_name"),
                    pr.get("head", {}).get("sha"),
                    "gemini/duplicate-detection",
                    duplicates_data,
                    token
                )
                
                return duplicates_data
            else:
                raise Exception(f"Duplicate detection failed: {response.status_code}")
    
    async def _trigger_code_review(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Trigger AI-powered code review"""
        pr = payload.get("pull_request", {})
        repository = payload.get("repository", {})
        
        # Get changed files
        changed_files = await self._get_pr_changed_files(
            repository.get("full_name"),
            pr.get("number"),
            token
        )
        
        # Send request for multi-agent code review
        review_request = {
            "id": f"review-pr-{pr.get('number')}-{datetime.utcnow().isoformat()}",
            "type": "qa",
            "action": "review_code",
            "payload": {
                "files": changed_files,
                "repository": repository.get("full_name"),
                "pr_number": pr.get("number"),
                "commit_sha": pr.get("head", {}).get("sha")
            },
            "context": {
                "github_event": "pull_request",
                "webhook_triggered": True,
                "review_type": "comprehensive"
            },
            "timeout": 240
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.agent_server_url}/api/v1/agent/request",
                json=review_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Create PR comment with review results
                await self._create_pr_comment(
                    repository.get("full_name"),
                    pr.get("number"),
                    self._format_review_comment(result),
                    token
                )
                
                return result
            else:
                raise Exception(f"Code review failed: {response.status_code}")
    
    async def _trigger_comprehensive_analysis(self, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Trigger comprehensive multi-agent analysis"""
        repository = payload.get("repository", {})
        
        # Trigger full project analysis
        analysis_request = {
            "id": f"comprehensive-{datetime.utcnow().isoformat()}",
            "type": "architect",
            "action": "comprehensive_analysis",
            "payload": {
                "repository": repository.get("full_name"),
                "analysis_scope": "project_wide",
                "include_all_agents": True
            },
            "context": {
                "github_event": "push",
                "webhook_triggered": True,
                "analysis_type": "comprehensive"
            },
            "timeout": 600
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.agent_server_url}/api/v1/agent/request",
                json=analysis_request,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Comprehensive analysis failed: {response.status_code}")
    
    async def _get_pr_changed_files(self, repo: str, pr_number: int, token: str) -> List[str]:
        """Get list of changed files in PR"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 200:
                files = response.json()
                return [f["filename"] for f in files]
            else:
                logger.error(f"Failed to get PR files: {response.status_code}")
                return []
    
    async def _update_pr_status(self, repo: str, commit_sha: str, context: str, 
                               result: Dict[str, Any], token: str):
        """Update PR status check"""
        # Determine status based on result
        if result.get("success"):
            if result.get("result", {}).get("issues"):
                issues = result["result"]["issues"]
                critical_issues = [i for i in issues if i.get("severity") == "critical"]
                
                if critical_issues:
                    state = "failure"
                    description = f"Found {len(critical_issues)} critical issues"
                else:
                    state = "success"
                    description = f"Found {len(issues)} issues for review"
            else:
                state = "success"
                description = "No issues detected"
        else:
            state = "error"
            description = "Analysis failed"
        
        status_data = {
            "state": state,
            "description": description,
            "context": context,
            "target_url": f"https://github.com/{repo}/actions"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repo}/statuses/{commit_sha}",
                json=status_data,
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to update status: {response.status_code}")
    
    async def _create_pr_comment(self, repo: str, pr_number: int, body: str, token: str):
        """Create or update PR comment"""
        # Check for existing Gemini comment
        async with httpx.AsyncClient() as client:
            # Get existing comments
            response = await client.get(
                f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            existing_comment = None
            if response.status_code == 200:
                comments = response.json()
                for comment in comments:
                    if "🤖 Gemini Enterprise Architect" in comment.get("body", ""):
                        existing_comment = comment
                        break
            
            # Update existing or create new comment
            if existing_comment:
                response = await client.patch(
                    f"https://api.github.com/repos/{repo}/issues/comments/{existing_comment['id']}",
                    json={"body": body},
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
            else:
                response = await client.post(
                    f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
                    json={"body": body},
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create/update comment: {response.status_code}")
    
    def _format_review_comment(self, result: Dict[str, Any]) -> str:
        """Format code review result as PR comment"""
        if not result.get("success"):
            return "🤖 **Gemini Enterprise Architect Analysis Failed**\n\nUnable to complete code review analysis."
        
        review_data = result.get("result", {})
        issues = review_data.get("issues", [])
        suggestions = review_data.get("suggestions", [])
        
        comment = "🤖 **Gemini Enterprise Architect - AI Code Review**\n\n"
        
        # Summary
        comment += f"**Analysis Summary:**\n"
        comment += f"- Issues found: {len(issues)}\n"
        comment += f"- Suggestions: {len(suggestions)}\n\n"
        
        # Critical issues
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if critical_issues:
            comment += "🚨 **Critical Issues:**\n"
            for issue in critical_issues[:3]:
                comment += f"- **{issue.get('type', 'Issue')}**: {issue.get('description', 'No description')}\n"
                if issue.get('file') and issue.get('line'):
                    comment += f"  📁 `{issue['file']}:{issue['line']}`\n"
                if issue.get('recommendation'):
                    comment += f"  💡 {issue['recommendation']}\n"
            comment += "\n"
        
        # Suggestions
        if suggestions:
            comment += "💡 **Suggestions:**\n"
            for suggestion in suggestions[:3]:
                comment += f"- {suggestion.get('description', 'No description')}\n"
            comment += "\n"
        
        if not issues and not suggestions:
            comment += "✅ **Great job!** No significant issues found.\n\n"
        
        comment += "---\n*Powered by Gemini Enterprise Architect Multi-Agent System*"
        
        return comment

# Initialize FastAPI app
app = FastAPI(title="Gemini GitHub App", version="1.0.0")

# Load configuration
config = GitHubAppConfig(
    app_id=os.environ["GITHUB_APP_ID"],
    private_key=os.environ["GITHUB_PRIVATE_KEY"],
    webhook_secret=os.environ["GITHUB_WEBHOOK_SECRET"],
    agent_server_url=os.environ.get("AGENT_SERVER_URL", "http://localhost:8000")
)

auth = GitHubAppAuth(config)
webhook_handler = WebhookHandler(config, auth)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Gemini GitHub App",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    payload = await request.body()
    if not webhook_handler.verify_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse payload
    event_type = request.headers.get("X-GitHub-Event")
    data = json.loads(payload)
    installation_id = data.get("installation", {}).get("id")
    
    if not installation_id:
        raise HTTPException(status_code=400, detail="Missing installation ID")
    
    logger.info(f"Received {event_type} event for installation {installation_id}")
    
    # Handle different event types
    try:
        if event_type == "pull_request":
            result = await webhook_handler.handle_pull_request(data, str(installation_id))
        elif event_type == "push":
            result = await webhook_handler.handle_push(data, str(installation_id))
        else:
            result = {"message": f"Event {event_type} not handled"}
        
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error handling {event_type} event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/installation/{installation_id}/status")
async def get_installation_status(installation_id: str):
    """Get installation status"""
    try:
        token = await auth.get_installation_token(installation_id)
        return {
            "installation_id": installation_id,
            "status": "active",
            "token_generated": True
        }
    except Exception as e:
        return {
            "installation_id": installation_id,
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        reload=True
    )