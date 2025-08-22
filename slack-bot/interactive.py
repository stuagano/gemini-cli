"""
Interactive Slack UI Components for Gemini Enterprise Architect
Handles buttons, modals, forms, and other interactive elements
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from slack_bolt.async_app import AsyncApp
from slack_sdk.errors import SlackApiError

from .app import agent_client, formatter, get_operation, store_operation, config

logger = logging.getLogger(__name__)

def register_interactive_components(slack_app: AsyncApp):
    """Register all interactive components with the Slack app"""
    
    # Button action handlers
    @slack_app.action("get_recommendations")
    async def handle_get_recommendations(ack, body, client):
        """Handle get recommendations button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "analysis")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Analysis data not found. Please run the analysis again."
            )
            return
        
        try:
            # Get detailed recommendations
            payload = {
                "target": operation['data']['target'],
                "analysis_result": operation['data']['result'],
                "recommendation_type": "detailed"
            }
            
            result = await agent_client.call_agent(
                agent_type="architect",
                action="generate_recommendations",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                blocks = _format_recommendations(result['result'])
                await client.chat_postMessage(
                    channel=body['channel']['id'],
                    blocks=blocks,
                    text="Detailed recommendations"
                )
            else:
                await client.chat_postEphemeral(
                    channel=body['channel']['id'],
                    user=user_id,
                    text="❌ Failed to generate recommendations"
                )
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error generating recommendations"
            )
    
    @slack_app.action("find_duplicates")
    async def handle_find_duplicates(ack, body, client):
        """Handle find duplicates button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "analysis")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Analysis data not found. Please run the analysis again."
            )
            return
        
        try:
            # Find duplicates using Scout
            payload = {
                "target": operation['data']['target'],
                "similarity_threshold": 0.7,
                "deep_analysis": True
            }
            
            result = await agent_client.call_agent(
                agent_type="scout",
                action="find_duplicates",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                blocks = _format_duplicates(result['result'])
                await client.chat_postMessage(
                    channel=body['channel']['id'],
                    blocks=blocks,
                    text="Duplicate analysis results"
                )
            else:
                await client.chat_postEphemeral(
                    channel=body['channel']['id'],
                    user=user_id,
                    text="❌ Failed to find duplicates"
                )
                
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error finding duplicates"
            )
    
    @slack_app.action("get_detailed_review")
    async def handle_get_detailed_review(ack, body, client):
        """Handle get detailed review button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "review")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Review data not found. Please run the review again."
            )
            return
        
        # Open modal for detailed review options
        modal_view = {
            "type": "modal",
            "callback_id": "detailed_review_modal",
            "title": {"type": "plain_text", "text": "Detailed Review Options"},
            "submit": {"type": "plain_text", "text": "Generate Report"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Select additional analysis options for your detailed review:"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Review Focus Areas:*"},
                    "accessory": {
                        "type": "checkboxes",
                        "action_id": "review_focus",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Security Analysis"}, "value": "security"},
                            {"text": {"type": "plain_text", "text": "Performance Impact"}, "value": "performance"},
                            {"text": {"type": "plain_text", "text": "Code Quality"}, "value": "quality"},
                            {"text": {"type": "plain_text", "text": "Architecture Compliance"}, "value": "architecture"},
                            {"text": {"type": "plain_text", "text": "Documentation Coverage"}, "value": "documentation"}
                        ]
                    }
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Report Format:*"},
                    "accessory": {
                        "type": "radio_buttons",
                        "action_id": "report_format",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Executive Summary"}, "value": "summary"},
                            {"text": {"type": "plain_text", "text": "Technical Details"}, "value": "technical"},
                            {"text": {"type": "plain_text", "text": "Full Report"}, "value": "full"}
                        ],
                        "initial_option": {"text": {"type": "plain_text", "text": "Technical Details"}, "value": "technical"}
                    }
                }
            ],
            "private_metadata": json.dumps({"user_id": user_id, "operation_type": "review"})
        }
        
        try:
            await client.views_open(
                trigger_id=body['trigger_id'],
                view=modal_view
            )
        except SlackApiError as e:
            logger.error(f"Error opening modal: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error opening detailed review options"
            )
    
    @slack_app.action("security_analysis")
    async def handle_security_analysis(ack, body, client):
        """Handle security analysis button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "review")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Review data not found. Please run the review again."
            )
            return
        
        try:
            # Run security-focused analysis
            payload = {
                "pr_url": operation['data']['pr_url'],
                "analysis_type": "security",
                "include_vulnerability_scan": True,
                "check_dependencies": True
            }
            
            result = await agent_client.call_agent(
                agent_type="qa",
                action="security_analysis",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                blocks = _format_security_analysis(result['result'])
                await client.chat_postMessage(
                    channel=body['channel']['id'],
                    blocks=blocks,
                    text="Security analysis results"
                )
            else:
                await client.chat_postEphemeral(
                    channel=body['channel']['id'],
                    user=user_id,
                    text="❌ Security analysis failed"
                )
                
        except Exception as e:
            logger.error(f"Error in security analysis: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error running security analysis"
            )
    
    @slack_app.action("get_killer_demo_report")
    async def handle_killer_demo_report(ack, body, client):
        """Handle killer demo report button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "killer_demo")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Killer demo data not found. Please run the analysis again."
            )
            return
        
        # Open modal for report customization
        modal_view = {
            "type": "modal",
            "callback_id": "killer_demo_report_modal",
            "title": {"type": "plain_text", "text": "Killer Demo Report"},
            "submit": {"type": "plain_text", "text": "Generate Report"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Customize your killer demo report:"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Include Sections:*"},
                    "accessory": {
                        "type": "checkboxes",
                        "action_id": "report_sections",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Performance Metrics"}, "value": "performance"},
                            {"text": {"type": "plain_text", "text": "Scaling Issues"}, "value": "scaling"},
                            {"text": {"type": "plain_text", "text": "Architecture Analysis"}, "value": "architecture"},
                            {"text": {"type": "plain_text", "text": "Code Quality"}, "value": "quality"},
                            {"text": {"type": "plain_text", "text": "Recommendations"}, "value": "recommendations"}
                        ],
                        "initial_options": [
                            {"text": {"type": "plain_text", "text": "Performance Metrics"}, "value": "performance"},
                            {"text": {"type": "plain_text", "text": "Scaling Issues"}, "value": "scaling"}
                        ]
                    }
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Report Detail Level:*"},
                    "accessory": {
                        "type": "static_select",
                        "action_id": "detail_level",
                        "placeholder": {"type": "plain_text", "text": "Select detail level"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Executive Summary"}, "value": "executive"},
                            {"text": {"type": "plain_text", "text": "Technical Overview"}, "value": "technical"},
                            {"text": {"type": "plain_text", "text": "Detailed Analysis"}, "value": "detailed"},
                            {"text": {"type": "plain_text", "text": "Complete Report"}, "value": "complete"}
                        ],
                        "initial_option": {"text": {"type": "plain_text", "text": "Technical Overview"}, "value": "technical"}
                    }
                }
            ],
            "private_metadata": json.dumps({"user_id": user_id, "operation_type": "killer_demo"})
        }
        
        try:
            await client.views_open(
                trigger_id=body['trigger_id'],
                view=modal_view
            )
        except SlackApiError as e:
            logger.error(f"Error opening killer demo modal: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error opening report options"
            )
    
    @slack_app.action("generate_architecture_diagram")
    async def handle_generate_diagram(ack, body, client):
        """Handle generate architecture diagram button"""
        await ack()
        
        user_id = body['user']['id']
        operation = get_operation(user_id, "architect")
        
        if not operation:
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Architecture data not found. Please run the architect command again."
            )
            return
        
        try:
            # Generate architecture diagram
            payload = {
                "requirements": operation['data']['requirements'],
                "architecture_result": operation['data']['result'],
                "diagram_type": "system_overview",
                "format": "mermaid"
            }
            
            result = await agent_client.call_agent(
                agent_type="architect",
                action="generate_diagram",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                diagram = result['result'].get('diagram', '')
                blocks = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🏗️ Architecture Diagram"}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```\n{diagram}\n```"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*💡 Tip:* Copy the diagram code above and paste it into a Mermaid renderer like GitHub or mermaid.live to visualize."
                        }
                    }
                ]
                
                await client.chat_postMessage(
                    channel=body['channel']['id'],
                    blocks=blocks,
                    text="Architecture diagram generated"
                )
            else:
                await client.chat_postEphemeral(
                    channel=body['channel']['id'],
                    user=user_id,
                    text="❌ Failed to generate architecture diagram"
                )
                
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            await client.chat_postEphemeral(
                channel=body['channel']['id'],
                user=user_id,
                text="❌ Error generating architecture diagram"
            )
    
    # Modal submission handlers
    @slack_app.view("detailed_review_modal")
    async def handle_detailed_review_submission(ack, body, client, view):
        """Handle detailed review modal submission"""
        await ack()
        
        metadata = json.loads(view['private_metadata'])
        user_id = metadata['user_id']
        
        # Extract form values
        values = view['state']['values']
        focus_areas = []
        report_format = "technical"
        
        for block_id, block_values in values.items():
            for action_id, action_value in block_values.items():
                if action_id == "review_focus" and action_value.get('selected_options'):
                    focus_areas = [opt['value'] for opt in action_value['selected_options']]
                elif action_id == "report_format" and action_value.get('selected_option'):
                    report_format = action_value['selected_option']['value']
        
        operation = get_operation(user_id, "review")
        if not operation:
            return
        
        try:
            # Generate detailed review
            payload = {
                "pr_url": operation['data']['pr_url'],
                "focus_areas": focus_areas,
                "report_format": report_format,
                "include_metrics": True
            }
            
            result = await agent_client.call_agent(
                agent_type="qa",
                action="detailed_review",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                blocks = _format_detailed_review(result['result'], focus_areas, report_format)
                await client.chat_postMessage(
                    channel=body['user']['id'],  # Send as DM
                    blocks=blocks,
                    text="Detailed review report"
                )
            else:
                await client.chat_postEphemeral(
                    channel=body['user']['id'],
                    user=user_id,
                    text="❌ Failed to generate detailed review"
                )
                
        except Exception as e:
            logger.error(f"Error generating detailed review: {e}")
            await client.chat_postMessage(
                channel=body['user']['id'],
                text="❌ Error generating detailed review report"
            )
    
    @slack_app.view("killer_demo_report_modal")
    async def handle_killer_demo_submission(ack, body, client, view):
        """Handle killer demo report modal submission"""
        await ack()
        
        metadata = json.loads(view['private_metadata'])
        user_id = metadata['user_id']
        
        # Extract form values
        values = view['state']['values']
        sections = []
        detail_level = "technical"
        
        for block_id, block_values in values.items():
            for action_id, action_value in block_values.items():
                if action_id == "report_sections" and action_value.get('selected_options'):
                    sections = [opt['value'] for opt in action_value['selected_options']]
                elif action_id == "detail_level" and action_value.get('selected_option'):
                    detail_level = action_value['selected_option']['value']
        
        operation = get_operation(user_id, "killer_demo")
        if not operation:
            return
        
        try:
            # Generate killer demo report
            payload = {
                "repository": operation['data']['repository'],
                "results": operation['data']['results'],
                "sections": sections,
                "detail_level": detail_level
            }
            
            result = await agent_client.call_agent(
                agent_type="analyst",
                action="generate_killer_demo_report",
                payload=payload,
                context={"source": "slack", "user_id": user_id}
            )
            
            if result['success']:
                blocks = _format_killer_demo_report(result['result'], sections, detail_level)
                await client.chat_postMessage(
                    channel=body['user']['id'],  # Send as DM
                    blocks=blocks,
                    text="Killer demo analysis report"
                )
            else:
                await client.chat_postMessage(
                    channel=body['user']['id'],
                    text="❌ Failed to generate killer demo report"
                )
                
        except Exception as e:
            logger.error(f"Error generating killer demo report: {e}")
            await client.chat_postMessage(
                channel=body['user']['id'],
                text="❌ Error generating killer demo report"
            )

def _format_recommendations(recommendations: Dict[str, Any]) -> List[Dict]:
    """Format recommendations for Slack display"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "💡 Detailed Recommendations"}
        },
        {
            "type": "divider"
        }
    ]
    
    if 'high_priority' in recommendations:
        high_priority = recommendations['high_priority'][:5]
        high_text = "\n".join([f"• {rec}" for rec in high_priority])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔴 High Priority:*\n{high_text}"
            }
        })
    
    if 'medium_priority' in recommendations:
        medium_priority = recommendations['medium_priority'][:3]
        medium_text = "\n".join([f"• {rec}" for rec in medium_priority])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🟡 Medium Priority:*\n{medium_text}"
            }
        })
    
    return blocks

def _format_duplicates(duplicates_data: Dict[str, Any]) -> List[Dict]:
    """Format duplicate analysis for Slack display"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔍 Duplicate Analysis Results"}
        },
        {
            "type": "divider"
        }
    ]
    
    duplicates = duplicates_data.get('duplicates', [])
    if duplicates:
        dup_text = ""
        for dup in duplicates[:10]:  # Show up to 10
            similarity = dup.get('similarity_score', 0)
            dup_text += f"• `{dup.get('function_name', 'Unknown')}` in {dup.get('duplicate_file', 'Unknown')} (similarity: {similarity:.0%})\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Found {len(duplicates)} potential duplicates:*\n{dup_text}"
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ No significant duplicates found in the analyzed code."
            }
        })
    
    return blocks

def _format_security_analysis(security_data: Dict[str, Any]) -> List[Dict]:
    """Format security analysis for Slack display"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔒 Security Analysis Results"}
        },
        {
            "type": "divider"
        }
    ]
    
    # Security score
    if 'security_score' in security_data:
        score = security_data['security_score']
        emoji = "🔒" if score >= 8 else "⚠️" if score >= 6 else "🚨"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *Security Score:* {score}/10"
            }
        })
    
    # Vulnerabilities
    if 'vulnerabilities' in security_data:
        vulns = security_data['vulnerabilities']
        if vulns:
            vuln_text = "\n".join([f"• {vuln['type']}: {vuln['description']}" for vuln in vulns[:5]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚨 Vulnerabilities Found:*\n{vuln_text}"
                }
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ No security vulnerabilities detected."
                }
            })
    
    return blocks

def _format_detailed_review(review_data: Dict[str, Any], focus_areas: List[str], report_format: str) -> List[Dict]:
    """Format detailed review report for Slack display"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📋 Detailed Review Report"}
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Focus Areas: {', '.join(focus_areas)} | Format: {report_format}"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    # Add sections based on focus areas
    for area in focus_areas:
        if area in review_data:
            area_data = review_data[area]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{area.replace('_', ' ').title()}:*\n{area_data.get('summary', 'No data available')}"
                }
            })
    
    return blocks

def _format_killer_demo_report(report_data: Dict[str, Any], sections: List[str], detail_level: str) -> List[Dict]:
    """Format killer demo report for Slack display"""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚀 Killer Demo Analysis Report"}
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sections: {', '.join(sections)} | Detail Level: {detail_level}"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    # Add report sections
    for section in sections:
        if section in report_data:
            section_data = report_data[section]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{section.replace('_', ' ').title()}:*\n{section_data.get('summary', 'Analysis in progress...')}"
                }
            })
    
    return blocks