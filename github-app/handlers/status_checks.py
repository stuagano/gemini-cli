"""
Status Check Handlers for Gemini GitHub App
Manages status check creation, updates, and coordination
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

class CheckStatus(Enum):
    """GitHub check status values"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class CheckConclusion(Enum):
    """GitHub check conclusion values"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    STALE = "stale"

@dataclass
class CheckOutput:
    """Check output data"""
    title: str
    summary: str
    text: Optional[str] = None
    annotations: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None

@dataclass
class StatusCheckConfig:
    """Configuration for status checks"""
    name: str
    context: str
    description: str
    target_url: Optional[str] = None
    required: bool = True
    timeout_minutes: int = 10

class StatusCheckManager:
    """Manages GitHub status checks and check runs"""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.active_checks: Dict[str, Dict[str, Any]] = {}
    
    async def create_check_run(self, repo: str, commit_sha: str, check_name: str, 
                              output: Optional[CheckOutput] = None) -> Dict[str, Any]:
        """Create a new check run"""
        check_data = {
            "name": check_name,
            "head_sha": commit_sha,
            "status": CheckStatus.QUEUED.value,
            "started_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if output:
            check_data["output"] = {
                "title": output.title,
                "summary": output.summary
            }
            if output.text:
                check_data["output"]["text"] = output.text
            if output.annotations:
                check_data["output"]["annotations"] = output.annotations
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repo}/check-runs",
                json=check_data,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 201:
                check = response.json()
                self.active_checks[f"{repo}#{commit_sha}#{check_name}"] = check
                logger.info(f"Created check run {check['id']} for {repo}@{commit_sha[:8]}")
                return check
            else:
                logger.error(f"Failed to create check run: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create check run: {response.status_code}")
    
    async def update_check_run(self, check_id: str, repo: str, 
                              status: CheckStatus = None,
                              conclusion: CheckConclusion = None,
                              output: CheckOutput = None) -> Dict[str, Any]:
        """Update an existing check run"""
        update_data = {}
        
        if status:
            update_data["status"] = status.value
            if status == CheckStatus.IN_PROGRESS:
                update_data["started_at"] = datetime.utcnow().isoformat() + "Z"
            elif status == CheckStatus.COMPLETED:
                update_data["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        if conclusion:
            update_data["conclusion"] = conclusion.value
            update_data["completed_at"] = datetime.utcnow().isoformat() + "Z"
        
        if output:
            update_data["output"] = {
                "title": output.title,
                "summary": output.summary
            }
            if output.text:
                update_data["output"]["text"] = output.text
            if output.annotations:
                update_data["output"]["annotations"] = output.annotations
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.github.com/repos/{repo}/check-runs/{check_id}",
                json=update_data,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Updated check run {check_id}")
                return response.json()
            else:
                logger.error(f"Failed to update check run: {response.status_code} - {response.text}")
                raise Exception(f"Failed to update check run: {response.status_code}")
    
    async def create_status_check(self, repo: str, commit_sha: str, context: str, 
                                 state: str, description: str, 
                                 target_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a status check (legacy API)"""
        status_data = {
            "state": state,
            "description": description,
            "context": context
        }
        
        if target_url:
            status_data["target_url"] = target_url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repo}/statuses/{commit_sha}",
                json=status_data,
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 201:
                logger.info(f"Created status check {context} for {repo}@{commit_sha[:8]}")
                return response.json()
            else:
                logger.error(f"Failed to create status check: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create status check: {response.status_code}")

class GeminiStatusChecks:
    """Gemini-specific status check implementations"""
    
    def __init__(self, status_manager: StatusCheckManager, agent_server_url: str):
        self.status_manager = status_manager
        self.agent_server_url = agent_server_url
        
        # Define Gemini status check configurations
        self.check_configs = [
            StatusCheckConfig(
                name="Killer Demo: Scaling Analysis",
                context="gemini/killer-demo-scaling",
                description="Detects N+1 queries, memory leaks, and performance issues",
                required=True,
                timeout_minutes=15
            ),
            StatusCheckConfig(
                name="Scout: Duplicate Detection",
                context="gemini/scout-duplicates",
                description="Prevents code duplication and promotes reuse",
                required=True,
                timeout_minutes=10
            ),
            StatusCheckConfig(
                name="Multi-Agent Code Review",
                context="gemini/code-review",
                description="AI-powered code quality analysis",
                required=True,
                timeout_minutes=20
            ),
            StatusCheckConfig(
                name="Guardian: Architecture Validation",
                context="gemini/guardian-validation",
                description="Validates architectural patterns and compliance",
                required=False,
                timeout_minutes=15
            ),
            StatusCheckConfig(
                name="Comprehensive Analysis",
                context="gemini/full-analysis",
                description="Complete multi-agent system analysis",
                required=False,
                timeout_minutes=30
            )
        ]
    
    async def run_killer_demo_scaling_check(self, repo: str, commit_sha: str, 
                                           changed_files: List[str]) -> Dict[str, Any]:
        """Run killer demo scaling analysis check"""
        config = next(c for c in self.check_configs if c.context == "gemini/killer-demo-scaling")
        
        # Create initial check
        check = await self.status_manager.create_check_run(
            repo, commit_sha, config.name,
            CheckOutput(
                title="🚀 Killer Demo: Scaling Analysis",
                summary="Starting scaling issue detection..."
            )
        )
        
        try:
            # Update to in progress
            await self.status_manager.update_check_run(
                check["id"], repo, CheckStatus.IN_PROGRESS,
                output=CheckOutput(
                    title="🚀 Killer Demo: Scaling Analysis",
                    summary="Analyzing code for scaling issues..."
                )
            )
            
            # Run scaling analysis
            analysis_result = await self._run_scaling_analysis(repo, commit_sha, changed_files)
            
            # Determine result
            if analysis_result.get("success"):
                issues = analysis_result.get("result", {}).get("issues", [])
                critical_issues = [i for i in issues if i.get("severity") == "critical"]
                risk_score = analysis_result.get("result", {}).get("risk_score", 0)
                
                if critical_issues:
                    conclusion = CheckConclusion.FAILURE
                    title = f"🔴 Critical Scaling Issues Found ({len(critical_issues)})"
                    summary = f"Found {len(critical_issues)} critical scaling issues that must be addressed."
                elif risk_score > 70:
                    conclusion = CheckConclusion.FAILURE
                    title = f"⚠️ High Risk Score ({risk_score}/100)"
                    summary = f"Risk score of {risk_score} exceeds threshold of 70."
                elif issues:
                    conclusion = CheckConclusion.SUCCESS
                    title = f"🟡 Scaling Issues Found ({len(issues)})"
                    summary = f"Found {len(issues)} scaling issues for review."
                else:
                    conclusion = CheckConclusion.SUCCESS
                    title = "✅ No Scaling Issues Detected"
                    summary = "Code appears well-optimized for production scaling."
                
                # Create detailed output
                annotations = []
                for issue in critical_issues[:10]:  # Limit annotations
                    if issue.get("file_path") and issue.get("line_number"):
                        annotations.append({
                            "path": issue["file_path"],
                            "start_line": issue["line_number"],
                            "end_line": issue["line_number"],
                            "annotation_level": "failure",
                            "message": issue.get("description", "Scaling issue detected"),
                            "title": f"{issue.get('type', 'Issue')} - {issue.get('severity', 'medium').title()}"
                        })
                
                detailed_text = self._format_scaling_analysis_text(analysis_result)
                
                await self.status_manager.update_check_run(
                    check["id"], repo, CheckStatus.COMPLETED, conclusion,
                    CheckOutput(
                        title=title,
                        summary=summary,
                        text=detailed_text,
                        annotations=annotations
                    )
                )
            else:
                await self.status_manager.update_check_run(
                    check["id"], repo, CheckStatus.COMPLETED, CheckConclusion.FAILURE,
                    CheckOutput(
                        title="❌ Scaling Analysis Failed",
                        summary="Unable to complete scaling analysis due to an error."
                    )
                )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Scaling analysis failed: {e}")
            await self.status_manager.update_check_run(
                check["id"], repo, CheckStatus.COMPLETED, CheckConclusion.FAILURE,
                CheckOutput(
                    title="❌ Analysis Error",
                    summary=f"Scaling analysis failed: {str(e)}"
                )
            )
            raise
    
    async def run_scout_duplicate_check(self, repo: str, commit_sha: str, 
                                       changed_files: List[str]) -> Dict[str, Any]:
        """Run Scout duplicate detection check"""
        config = next(c for c in self.check_configs if c.context == "gemini/scout-duplicates")
        
        # Create initial check
        check = await self.status_manager.create_check_run(
            repo, commit_sha, config.name,
            CheckOutput(
                title="🔍 Scout: Duplicate Detection",
                summary="Starting duplicate code detection..."
            )
        )
        
        try:
            # Update to in progress
            await self.status_manager.update_check_run(
                check["id"], repo, CheckStatus.IN_PROGRESS,
                output=CheckOutput(
                    title="🔍 Scout: Duplicate Detection",
                    summary="Scanning for duplicate code..."
                )
            )
            
            # Run duplicate detection
            duplicate_result = await self._run_duplicate_detection()
            
            # Analyze results
            duplicates = duplicate_result.get("duplicates", [])
            total_count = duplicate_result.get("total_count", 0)
            
            # Filter duplicates involving changed files
            relevant_duplicates = []
            for dup in duplicates:
                if any(f in dup.get("original_file", "") or f in dup.get("duplicate_file", "") 
                       for f in changed_files):
                    relevant_duplicates.append(dup)
            
            if relevant_duplicates:
                high_similarity = [d for d in relevant_duplicates if d.get("similarity_score", 0) > 0.9]
                
                if high_similarity:
                    conclusion = CheckConclusion.FAILURE
                    title = f"🔴 High Similarity Duplicates ({len(high_similarity)})"
                    summary = f"Found {len(high_similarity)} high-similarity duplicates in changed files."
                else:
                    conclusion = CheckConclusion.SUCCESS
                    title = f"🟡 Duplicates Detected ({len(relevant_duplicates)})"
                    summary = f"Found {len(relevant_duplicates)} potential duplicates for review."
            else:
                conclusion = CheckConclusion.SUCCESS
                title = "✅ No Duplicates in Changes"
                summary = "No duplicate code detected in modified files."
            
            # Create annotations for duplicates
            annotations = []
            for dup in relevant_duplicates[:5]:  # Limit annotations
                if dup.get("duplicate_file") in changed_files:
                    annotations.append({
                        "path": dup["duplicate_file"],
                        "start_line": dup.get("line_start", 1),
                        "end_line": dup.get("line_end", 1),
                        "annotation_level": "warning",
                        "message": f"Duplicate of {dup.get('original_file', 'unknown')} (similarity: {dup.get('similarity_score', 0):.2f})",
                        "title": f"Duplicate Function: {dup.get('function_name', 'unknown')}"
                    })
            
            detailed_text = self._format_duplicate_detection_text(duplicate_result, relevant_duplicates)
            
            await self.status_manager.update_check_run(
                check["id"], repo, CheckStatus.COMPLETED, conclusion,
                CheckOutput(
                    title=title,
                    summary=summary,
                    text=detailed_text,
                    annotations=annotations
                )
            )
            
            return {
                "success": True,
                "result": {
                    "total_duplicates": total_count,
                    "relevant_duplicates": len(relevant_duplicates),
                    "high_similarity": len([d for d in relevant_duplicates if d.get("similarity_score", 0) > 0.9])
                }
            }
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            await self.status_manager.update_check_run(
                check["id"], repo, CheckStatus.COMPLETED, CheckConclusion.FAILURE,
                CheckOutput(
                    title="❌ Detection Error",
                    summary=f"Duplicate detection failed: {str(e)}"
                )
            )
            raise
    
    async def _run_scaling_analysis(self, repo: str, commit_sha: str, 
                                   changed_files: List[str]) -> Dict[str, Any]:
        """Run scaling analysis via agent server"""
        analysis_request = {
            "id": f"scaling-check-{commit_sha[:8]}",
            "type": "developer",
            "action": "analyze_scaling",
            "payload": {
                "files": changed_files,
                "repository": repo,
                "commit_sha": commit_sha,
                "severity_threshold": "medium"
            },
            "context": {
                "check_run": True,
                "killer_demo": True
            },
            "timeout": 300
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.agent_server_url}/api/v1/agent/request",
                json=analysis_request,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Scaling analysis request failed: {response.status_code}")
    
    async def _run_duplicate_detection(self) -> Dict[str, Any]:
        """Run duplicate detection via Scout endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.agent_server_url}/api/v1/scout/duplicates",
                params={"similarity_threshold": 0.8},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Duplicate detection request failed: {response.status_code}")
    
    def _format_scaling_analysis_text(self, result: Dict[str, Any]) -> str:
        """Format scaling analysis result as detailed text"""
        if not result.get("success"):
            return "❌ Scaling analysis failed to complete."
        
        analysis = result.get("result", {})
        issues = analysis.get("issues", [])
        risk_score = analysis.get("risk_score", 0)
        production_ready = analysis.get("production_readiness", False)
        
        text = f"## 🚀 Killer Demo: Scaling Analysis Results\n\n"
        text += f"**Risk Score:** {risk_score}/100\n"
        text += f"**Production Ready:** {'✅ Yes' if production_ready else '❌ No'}\n"
        text += f"**Total Issues:** {len(issues)}\n\n"
        
        if issues:
            text += "### Issues Detected\n\n"
            issue_types = {}
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)
            
            for issue_type, type_issues in issue_types.items():
                text += f"#### {issue_type.replace('_', ' ').title()} ({len(type_issues)})\n"
                for issue in type_issues[:3]:  # Limit detail
                    text += f"- **{issue.get('severity', 'medium').title()}**: {issue.get('description', 'No description')}\n"
                    if issue.get('fix_recommendation'):
                        text += f"  💡 {issue['fix_recommendation']}\n"
                text += "\n"
        else:
            text += "✅ No scaling issues detected. Code appears well-optimized for production.\n"
        
        return text
    
    def _format_duplicate_detection_text(self, result: Dict[str, Any], 
                                        relevant_duplicates: List[Dict[str, Any]]) -> str:
        """Format duplicate detection result as detailed text"""
        total_count = result.get("total_count", 0)
        threshold = result.get("similarity_threshold", 0.8)
        
        text = f"## 🔍 Scout: Duplicate Detection Results\n\n"
        text += f"**Similarity Threshold:** {threshold}\n"
        text += f"**Total Project Duplicates:** {total_count}\n"
        text += f"**Relevant to Changes:** {len(relevant_duplicates)}\n\n"
        
        if relevant_duplicates:
            text += "### Duplicates in Changed Files\n\n"
            for dup in relevant_duplicates[:5]:  # Limit detail
                similarity = dup.get("similarity_score", 0)
                original = dup.get("original_file", "unknown")
                duplicate = dup.get("duplicate_file", "unknown")
                function = dup.get("function_name", "unknown")
                
                text += f"- **{function}** ({similarity:.2f} similarity)\n"
                text += f"  Original: `{original}`\n"
                text += f"  Duplicate: `{duplicate}`\n\n"
            
            if len(relevant_duplicates) > 5:
                text += f"... and {len(relevant_duplicates) - 5} more duplicates\n\n"
            
            text += "### Recommendations\n"
            text += "- Consider extracting common functionality into shared utilities\n"
            text += "- Review duplicate code for potential refactoring opportunities\n"
            text += "- Use Scout's indexing to identify reusable patterns\n"
        else:
            text += "✅ No duplicate code detected in the changed files.\n"
        
        return text