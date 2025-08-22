"""
Agent Router for intelligent request routing
Determines which agent should handle requests based on content and patterns
"""

from typing import Dict, Any, Optional, Type, List, Tuple
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class RoutingRule:
    """Rule for routing requests to specific agents"""
    pattern: str
    agent_type: str
    priority: int
    conditions: Dict[str, Any]
    keywords: List[str]

class AgentRouter:
    """Routes requests to appropriate agents based on content analysis"""
    
    def __init__(self):
        self.routes: List[RoutingRule] = self._initialize_routes()
        self.agent_capabilities = self._initialize_capabilities()
        
    def _initialize_routes(self) -> List[RoutingRule]:
        """Initialize routing rules"""
        return [
            # Scout routes - Always first for code analysis
            RoutingRule(
                pattern=r"(analyze|scan|check|review).*code",
                agent_type="scout",
                priority=0,
                conditions={"requires_codebase_analysis": True},
                keywords=["duplicate", "DRY", "reuse", "existing", "pattern", "dependency"]
            ),
            
            # Analyst routes
            RoutingRule(
                pattern=r"(research|analyze|investigate|study|market|competitive)",
                agent_type="analyst",
                priority=1,
                conditions={"phase": "planning"},
                keywords=["market", "research", "analysis", "competition", "trends", "requirements"]
            ),
            
            # PM routes
            RoutingRule(
                pattern=r"(product|requirement|PRD|roadmap|feature|epic|story)",
                agent_type="pm",
                priority=1,
                conditions={"document_type": "prd"},
                keywords=["PRD", "product", "requirements", "user story", "epic", "feature", "roadmap"]
            ),
            
            # Architect routes
            RoutingRule(
                pattern=r"(architect|design|system|infrastructure|scale|service)",
                agent_type="architect",
                priority=1,
                conditions={"requires_technical_design": True},
                keywords=["architecture", "design", "GCP", "service", "infrastructure", "scaling", "database"]
            ),
            
            # Developer routes
            RoutingRule(
                pattern=r"(implement|code|build|create|develop|fix|debug)",
                agent_type="developer",
                priority=2,
                conditions={"phase": "implementation"},
                keywords=["implement", "code", "build", "function", "class", "API", "endpoint", "fix", "bug"]
            ),
            
            # QA routes
            RoutingRule(
                pattern=r"(test|validate|verify|quality|review.*code|check.*quality)",
                agent_type="qa",
                priority=2,
                conditions={"requires_validation": True},
                keywords=["test", "quality", "validate", "verify", "coverage", "regression", "review"]
            ),
            
            # PO routes
            RoutingRule(
                pattern=r"(prioritize|backlog|value|ROI|stakeholder|approve)",
                agent_type="po",
                priority=1,
                conditions={"requires_business_decision": True},
                keywords=["prioritize", "backlog", "value", "ROI", "stakeholder", "approve", "acceptance"]
            )
        ]
    
    def _initialize_capabilities(self) -> Dict[str, List[str]]:
        """Initialize agent capabilities"""
        return {
            "scout": [
                "codebase_analysis",
                "duplication_detection",
                "dependency_mapping",
                "pattern_recognition",
                "technical_debt_analysis"
            ],
            "analyst": [
                "market_research",
                "competitive_analysis",
                "requirements_gathering",
                "user_research",
                "trend_analysis"
            ],
            "pm": [
                "prd_creation",
                "story_writing",
                "roadmap_planning",
                "feature_definition",
                "requirement_documentation"
            ],
            "architect": [
                "system_design",
                "service_selection",
                "infrastructure_planning",
                "scalability_analysis",
                "technical_architecture"
            ],
            "developer": [
                "code_generation",
                "implementation",
                "debugging",
                "refactoring",
                "api_development"
            ],
            "qa": [
                "test_planning",
                "test_execution",
                "quality_validation",
                "regression_testing",
                "code_review"
            ],
            "po": [
                "backlog_management",
                "prioritization",
                "value_analysis",
                "stakeholder_alignment",
                "acceptance_validation"
            ]
        }
    
    def route_request(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine which agent should handle the request"""
        query = payload.get("query", "")
        full_text = f"{action} {query}".lower()
        
        # Check for explicit agent specification
        if "agent" in context:
            return context["agent"]
        
        # Analyze intent
        intent = self.analyze_intent(full_text)
        
        # Score each route based on pattern matching and keywords
        route_scores = []
        for rule in self.routes:
            score = self._calculate_route_score(rule, full_text, intent, context)
            if score > 0:
                route_scores.append((rule, score))
        
        # Sort by score (higher is better) and priority (lower is better)
        route_scores.sort(key=lambda x: (-x[1], x[0].priority))
        
        if route_scores:
            best_route = route_scores[0][0]
            logger.info(f"Routing to {best_route.agent_type} (score: {route_scores[0][1]})")
            return best_route.agent_type
        
        # Default routing based on action
        return self.default_agent_for_action(action)
    
    def _calculate_route_score(self, rule: RoutingRule, text: str, 
                              intent: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate matching score for a routing rule"""
        score = 0.0
        
        # Pattern matching
        if re.search(rule.pattern, text):
            score += 3.0
        
        # Keyword matching
        keyword_matches = sum(1 for keyword in rule.keywords if keyword in text)
        score += keyword_matches * 0.5
        
        # Condition matching
        conditions_met = all(
            context.get(key) == value 
            for key, value in rule.conditions.items()
        )
        if conditions_met:
            score += 2.0
        
        # Intent alignment
        if intent.get("primary") in rule.keywords:
            score += 1.5
        
        return score
    
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analyze the intent of a query"""
        intents = {
            "research": ["analyze", "research", "investigate", "study", "explore", "examine"],
            "create": ["build", "create", "generate", "make", "implement", "develop"],
            "test": ["test", "validate", "verify", "check", "ensure", "confirm"],
            "deploy": ["deploy", "release", "ship", "publish", "launch"],
            "optimize": ["optimize", "improve", "enhance", "refactor", "performance"],
            "design": ["design", "architect", "plan", "structure", "organize"],
            "manage": ["manage", "prioritize", "organize", "coordinate", "oversee"]
        }
        
        detected_intent = "general"
        confidence = 0.0
        
        for intent, keywords in intents.items():
            matches = sum(1 for keyword in keywords if keyword in query.lower())
            if matches > 0:
                match_confidence = matches / len(keywords)
                if match_confidence > confidence:
                    detected_intent = intent
                    confidence = match_confidence
        
        return {
            "primary": detected_intent,
            "confidence": confidence,
            "raw_query": query
        }
    
    def orchestrate_workflow(self, action: str, payload: Dict[str, Any]) -> List[str]:
        """Determine multi-agent workflow for complex tasks"""
        workflows = {
            "full_development": ["scout", "analyst", "pm", "architect", "developer", "qa", "po"],
            "bug_fix": ["scout", "developer", "qa"],
            "feature_addition": ["analyst", "pm", "scout", "architect", "developer", "qa"],
            "research_task": ["analyst", "architect"],
            "deployment": ["qa", "po", "developer"],
            "architecture_review": ["scout", "architect", "qa"],
            "performance_optimization": ["scout", "architect", "developer", "qa"]
        }
        
        # Determine workflow type based on action and payload
        workflow_type = self.determine_workflow_type(action, payload)
        return workflows.get(workflow_type, ["analyst"])
    
    def determine_workflow_type(self, action: str, payload: Dict[str, Any]) -> str:
        """Determine the type of workflow needed"""
        query = payload.get("query", "").lower()
        
        if "bug" in query or "fix" in query or "error" in query:
            return "bug_fix"
        elif "feature" in query or "add" in query or "new" in query:
            return "feature_addition"
        elif "deploy" in query or "release" in query:
            return "deployment"
        elif "research" in query or "analyze" in query:
            return "research_task"
        elif "architecture" in query or "design" in query:
            return "architecture_review"
        elif "performance" in query or "optimize" in query:
            return "performance_optimization"
        elif "full" in query or "complete" in query or "entire" in query:
            return "full_development"
        
        return "research_task"  # Default
    
    def default_agent_for_action(self, action: str) -> str:
        """Get default agent for a given action"""
        action_defaults = {
            "analyze": "analyst",
            "research": "analyst",
            "create": "developer",
            "implement": "developer",
            "test": "qa",
            "validate": "qa",
            "design": "architect",
            "plan": "pm",
            "prioritize": "po",
            "review": "qa"
        }
        
        # Check if action contains any default keywords
        for keyword, agent in action_defaults.items():
            if keyword in action.lower():
                return agent
        
        # Ultimate default
        return "analyst"
    
    def get_agent_chain(self, initial_agent: str, task_type: str) -> List[str]:
        """Get the chain of agents for a multi-step task"""
        chains = {
            "scout": {
                "analysis": ["scout", "architect", "developer"],
                "validation": ["scout", "qa"],
                "implementation": ["scout", "developer", "qa"]
            },
            "analyst": {
                "research": ["analyst", "pm"],
                "requirements": ["analyst", "pm", "architect"],
                "planning": ["analyst", "pm", "po"]
            },
            "pm": {
                "planning": ["pm", "architect", "po"],
                "story_creation": ["pm", "developer"],
                "roadmap": ["pm", "po"]
            },
            "architect": {
                "design": ["architect", "developer"],
                "review": ["architect", "qa"],
                "optimization": ["architect", "scout", "developer"]
            },
            "developer": {
                "implementation": ["developer", "qa"],
                "bug_fix": ["developer", "qa"],
                "refactoring": ["scout", "developer", "qa"]
            },
            "qa": {
                "testing": ["qa"],
                "validation": ["qa", "po"],
                "regression": ["qa", "developer"]
            },
            "po": {
                "prioritization": ["po", "pm"],
                "approval": ["po"],
                "planning": ["po", "pm", "analyst"]
            }
        }
        
        agent_chains = chains.get(initial_agent, {})
        return agent_chains.get(task_type, [initial_agent])
    
    def validate_agent_sequence(self, agents: List[str]) -> Tuple[bool, str]:
        """Validate if a sequence of agents makes sense"""
        # Define valid transitions
        valid_transitions = {
            "analyst": ["pm", "architect", "po"],
            "pm": ["architect", "developer", "po", "analyst"],
            "architect": ["developer", "qa", "scout"],
            "scout": ["developer", "architect", "qa"],
            "developer": ["qa", "scout"],
            "qa": ["developer", "po", "architect"],
            "po": ["pm", "analyst", "developer"]
        }
        
        # Check each transition
        for i in range(len(agents) - 1):
            current = agents[i]
            next_agent = agents[i + 1]
            
            if current not in valid_transitions:
                return False, f"Unknown agent: {current}"
            
            if next_agent not in valid_transitions[current]:
                return False, f"Invalid transition: {current} -> {next_agent}"
        
        return True, "Valid sequence"
    
    def suggest_next_agent(self, current_agent: str, context: Dict[str, Any]) -> Optional[str]:
        """Suggest the next agent based on current agent and context"""
        suggestions = {
            "analyst": {
                "needs_requirements": "pm",
                "needs_architecture": "architect",
                "needs_approval": "po"
            },
            "pm": {
                "needs_technical_design": "architect",
                "needs_implementation": "developer",
                "needs_validation": "po"
            },
            "architect": {
                "needs_code_analysis": "scout",
                "needs_implementation": "developer",
                "needs_review": "qa"
            },
            "scout": {
                "found_duplicates": "architect",
                "needs_refactoring": "developer",
                "needs_validation": "qa"
            },
            "developer": {
                "needs_testing": "qa",
                "needs_analysis": "scout",
                "completed": "qa"
            },
            "qa": {
                "found_issues": "developer",
                "needs_approval": "po",
                "passed": "po"
            },
            "po": {
                "needs_changes": "pm",
                "approved": None,
                "needs_analysis": "analyst"
            }
        }
        
        agent_suggestions = suggestions.get(current_agent, {})
        
        # Check context for conditions
        for condition, next_agent in agent_suggestions.items():
            if condition in context and context[condition]:
                return next_agent
        
        # Default suggestions
        defaults = {
            "analyst": "pm",
            "pm": "architect",
            "architect": "developer",
            "scout": "developer",
            "developer": "qa",
            "qa": "po",
            "po": None
        }
        
        return defaults.get(current_agent)