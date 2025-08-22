"""
Slash Command Handlers for Gemini Enterprise Architect Slack Bot
Implements all slash commands for agent interactions
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

from .app import agent_client, formatter, store_operation, active_operations, config

logger = logging.getLogger(__name__)

def register_commands(slack_app: AsyncApp):
    """Register all slash commands with the Slack app"""
    
    @slack_app.command("/gemini-analyze")
    async def handle_analyze_command(ack, respond, command):
        """Handle /gemini-analyze [code/file] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please provide code or file path to analyze.\nUsage: `/gemini-analyze <code or file path>`"
            })
            return
        
        # Show loading message
        await respond({
            "response_type": "ephemeral",
            "text": "🔍 Analyzing code... This may take a moment."
        })
        
        try:
            # Determine if it's a file path or code
            is_file_path = ('/' in text or '\\' in text) and not text.startswith('```')
            
            payload = {
                "target": text,
                "analysis_type": "file" if is_file_path else "code",
                "include_suggestions": True,
                "check_duplicates": True
            }
            
            # Call analyst agent
            result = await agent_client.call_agent(
                agent_type="analyst",
                action="analyze_code",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                # Format and send results
                response = formatter.format_code_analysis(result)
                response["response_type"] = "in_channel"
                
                # Add follow-up actions
                response["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Get Recommendations"},
                            "value": f"recommendations_{user_id}",
                            "action_id": "get_recommendations"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Find Duplicates"},
                            "value": f"duplicates_{user_id}",
                            "action_id": "find_duplicates"
                        }
                    ]
                })
                
                # Store operation for follow-up
                store_operation(user_id, "analysis", {
                    "target": text,
                    "result": result,
                    "is_file_path": is_file_path
                })
                
                await respond(response)
            else:
                error_msg = result.get('error', {}).get('message', 'Analysis failed')
                await respond(formatter.format_error(error_msg, "analyst"))
                
        except Exception as e:
            logger.error(f"Error in analyze command: {e}")
            await respond(formatter.format_error(f"Failed to analyze code: {str(e)}"))
    
    @slack_app.command("/gemini-review")
    async def handle_review_command(ack, respond, command):
        """Handle /gemini-review [PR-URL] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please provide a PR URL to review.\nUsage: `/gemini-review <github-pr-url>`"
            })
            return
        
        # Validate URL
        try:
            parsed_url = urlparse(text)
            if 'github.com' not in parsed_url.netloc or '/pull/' not in parsed_url.path:
                await respond({
                    "response_type": "ephemeral",
                    "text": "Please provide a valid GitHub PR URL.\nExample: `https://github.com/owner/repo/pull/123`"
                })
                return
        except:
            await respond({
                "response_type": "ephemeral",
                "text": "Invalid URL format. Please provide a valid GitHub PR URL."
            })
            return
        
        await respond({
            "response_type": "ephemeral",
            "text": "📋 Reviewing pull request... This may take a moment."
        })
        
        try:
            payload = {
                "pr_url": text,
                "review_type": "comprehensive",
                "include_security_check": True,
                "include_performance_analysis": True
            }
            
            # Use multiple agents for comprehensive review
            qa_result = await agent_client.call_agent(
                agent_type="qa",
                action="review_pr",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            architect_result = await agent_client.call_agent(
                agent_type="architect",
                action="review_architecture",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if qa_result['success']:
                response = formatter.format_pr_review(qa_result)
                response["response_type"] = "in_channel"
                
                # Add architecture insights if available
                if architect_result['success']:
                    arch_insights = architect_result.get('result', {}).get('insights', [])
                    if arch_insights:
                        response["blocks"].append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Architecture Insights:*\n" + "\n".join([f"• {insight}" for insight in arch_insights[:3]])
                            }
                        })
                
                # Add follow-up actions
                response["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Detailed Report"},
                            "value": f"detailed_review_{user_id}",
                            "action_id": "get_detailed_review"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Security Analysis"},
                            "value": f"security_{user_id}",
                            "action_id": "security_analysis"
                        }
                    ]
                })
                
                # Store operation
                store_operation(user_id, "review", {
                    "pr_url": text,
                    "qa_result": qa_result,
                    "architect_result": architect_result
                })
                
                await respond(response)
            else:
                error_msg = qa_result.get('error', {}).get('message', 'Review failed')
                await respond(formatter.format_error(error_msg, "qa"))
                
        except Exception as e:
            logger.error(f"Error in review command: {e}")
            await respond(formatter.format_error(f"Failed to review PR: {str(e)}"))
    
    @slack_app.command("/gemini-ask")
    async def handle_ask_command(ack, respond, command):
        """Handle /gemini-ask [question] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please ask a question.\nUsage: `/gemini-ask <your question>`"
            })
            return
        
        await respond({
            "response_type": "ephemeral",
            "text": "🤔 Thinking... Let me find the best agent to answer your question."
        })
        
        try:
            # Determine which agent to use based on question content
            agent_type = _determine_agent_for_question(text)
            
            payload = {
                "question": text,
                "context": "slack_conversation",
                "provide_examples": True
            }
            
            result = await agent_client.call_agent(
                agent_type=agent_type,
                action="answer_question",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                response = formatter.format_agent_response(agent_type, result)
                response["response_type"] = "in_channel"
                
                # Add agent attribution
                response["blocks"].insert(0, {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Answered by *{agent_type.capitalize()} Agent*"
                        }
                    ]
                })
                
                await respond(response)
            else:
                error_msg = result.get('error', {}).get('message', 'Failed to answer question')
                await respond(formatter.format_error(error_msg, agent_type))
                
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            await respond(formatter.format_error(f"Failed to process question: {str(e)}"))
    
    @slack_app.command("/gemini-killer-demo")
    async def handle_killer_demo_command(ack, respond, command):
        """Handle /gemini-killer-demo [repo] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please provide a repository path or URL.\nUsage: `/gemini-killer-demo <repo-path-or-url>`"
            })
            return
        
        await respond({
            "response_type": "ephemeral",
            "text": "🚀 Running killer demo scaling analysis... This will take a few minutes."
        })
        
        try:
            payload = {
                "repository": text,
                "scaling_metrics": ["performance", "architecture", "maintainability"],
                "include_recommendations": True,
                "critical_issues_only": False
            }
            
            # Use specialist agents for comprehensive analysis
            analyst_task = agent_client.call_agent("analyst", "scaling_analysis", payload, {"source": "slack", "user_id": user_id})
            architect_task = agent_client.call_agent("architect", "architecture_review", payload, {"source": "slack", "user_id": user_id})
            scout_task = agent_client.call_agent("scout", "find_scaling_issues", payload, {"source": "slack", "user_id": user_id})
            
            # Run in parallel
            results = await asyncio.gather(analyst_task, architect_task, scout_task, return_exceptions=True)
            
            blocks = [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🚀 Killer Demo Analysis Results"}
                },
                {
                    "type": "divider"
                }
            ]
            
            # Process results
            for i, (agent_name, result) in enumerate(zip(["Analyst", "Architect", "Scout"], results)):
                if isinstance(result, Exception):
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *{agent_name}:* Analysis failed - {str(result)}"
                        }
                    })
                elif result.get('success'):
                    data = result.get('result', {})
                    summary = data.get('summary', 'Analysis completed')
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *{agent_name}:* {summary}"
                        }
                    })
            
            # Add follow-up actions
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Full Report"},
                        "value": f"killer_demo_report_{user_id}",
                        "action_id": "get_killer_demo_report"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Critical Issues Only"},
                        "value": f"critical_issues_{user_id}",
                        "action_id": "get_critical_issues"
                    }
                ]
            })
            
            store_operation(user_id, "killer_demo", {
                "repository": text,
                "results": results
            })
            
            await respond({
                "response_type": "in_channel",
                "blocks": blocks
            })
            
        except Exception as e:
            logger.error(f"Error in killer-demo command: {e}")
            await respond(formatter.format_error(f"Failed to run killer demo analysis: {str(e)}"))
    
    @slack_app.command("/gemini-scout")
    async def handle_scout_command(ack, respond, command):
        """Handle /gemini-scout [search] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please provide search criteria.\nUsage: `/gemini-scout <search terms or pattern>`"
            })
            return
        
        await respond({
            "response_type": "ephemeral",
            "text": "🔍 Scout is searching for duplicates and patterns..."
        })
        
        try:
            payload = {
                "search_terms": text,
                "find_duplicates": True,
                "find_patterns": True,
                "similarity_threshold": 0.8
            }
            
            result = await agent_client.call_agent(
                agent_type="scout",
                action="search_codebase",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                data = result.get('result', {})
                
                blocks = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🔍 Scout Search Results"}
                    },
                    {
                        "type": "divider"
                    }
                ]
                
                # Duplicates found
                if data.get('duplicates'):
                    duplicates = data['duplicates'][:5]  # Limit to 5
                    dup_text = "\n".join([
                        f"• `{d.get('function_name', 'Unknown')}` in {d.get('file', 'Unknown')} (similarity: {d.get('similarity', 0):.0%})"
                        for d in duplicates
                    ])
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Duplicates Found ({len(data['duplicates'])} total):*\n{dup_text}"
                        }
                    })
                
                # Patterns found
                if data.get('patterns'):
                    patterns = data['patterns'][:3]  # Limit to 3
                    pattern_text = "\n".join([f"• {pattern}" for pattern in patterns])
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Patterns Found:*\n{pattern_text}"
                        }
                    })
                
                # Add actions
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Detailed Analysis"},
                            "value": f"scout_detailed_{user_id}",
                            "action_id": "get_scout_detailed"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Export Results"},
                            "value": f"scout_export_{user_id}",
                            "action_id": "export_scout_results"
                        }
                    ]
                })
                
                store_operation(user_id, "scout", {
                    "search_terms": text,
                    "result": result
                })
                
                await respond({
                    "response_type": "in_channel",
                    "blocks": blocks
                })
            else:
                error_msg = result.get('error', {}).get('message', 'Scout search failed')
                await respond(formatter.format_error(error_msg, "scout"))
                
        except Exception as e:
            logger.error(f"Error in scout command: {e}")
            await respond(formatter.format_error(f"Scout search failed: {str(e)}"))
    
    @slack_app.command("/gemini-architect")
    async def handle_architect_command(ack, respond, command):
        """Handle /gemini-architect [requirements] command"""
        await ack()
        
        user_id = command['user_id']
        text = command.get('text', '').strip()
        
        if not text:
            await respond({
                "response_type": "ephemeral",
                "text": "Please provide architecture requirements.\nUsage: `/gemini-architect <your requirements>`"
            })
            return
        
        await respond({
            "response_type": "ephemeral",
            "text": "🏗️ Architect is analyzing requirements and designing architecture..."
        })
        
        try:
            payload = {
                "requirements": text,
                "architecture_type": "microservices",  # Default
                "include_patterns": True,
                "include_diagrams": True
            }
            
            result = await agent_client.call_agent(
                agent_type="architect",
                action="design_architecture",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                response = formatter.format_agent_response("architect", result)
                response["response_type"] = "in_channel"
                
                # Add architecture-specific actions
                response["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Generate Diagram"},
                            "value": f"arch_diagram_{user_id}",
                            "action_id": "generate_architecture_diagram"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Implementation Plan"},
                            "value": f"impl_plan_{user_id}",
                            "action_id": "get_implementation_plan"
                        }
                    ]
                })
                
                store_operation(user_id, "architect", {
                    "requirements": text,
                    "result": result
                })
                
                await respond(response)
            else:
                error_msg = result.get('error', {}).get('message', 'Architecture design failed')
                await respond(formatter.format_error(error_msg, "architect"))
                
        except Exception as e:
            logger.error(f"Error in architect command: {e}")
            await respond(formatter.format_error(f"Architecture design failed: {str(e)}"))

def _determine_agent_for_question(question: str) -> str:
    """Determine which agent should handle the question based on content"""
    question_lower = question.lower()
    
    # Keywords for each agent type
    keywords = {
        'architect': ['architecture', 'design', 'pattern', 'structure', 'system', 'scalability', 'microservices'],
        'developer': ['code', 'implementation', 'function', 'class', 'method', 'programming', 'syntax'],
        'qa': ['test', 'testing', 'quality', 'bug', 'defect', 'validation', 'verification'],
        'pm': ['project', 'timeline', 'planning', 'requirements', 'scope', 'milestone', 'delivery'],
        'analyst': ['performance', 'analysis', 'metrics', 'data', 'report', 'statistics'],
        'scout': ['duplicate', 'similar', 'pattern', 'search', 'find', 'locate'],
        'po': ['feature', 'product', 'user story', 'backlog', 'priority', 'value']
    }
    
    # Score each agent based on keyword matches
    scores = {}
    for agent, words in keywords.items():
        scores[agent] = sum(1 for word in words if word in question_lower)
    
    # Return agent with highest score, default to analyst
    best_agent = max(scores.items(), key=lambda x: x[1])
    return best_agent[0] if best_agent[1] > 0 else 'analyst'