"""
Natural Language CLI Interface
Enables developers to interact with Gemini using intuitive commands
Epic 1: Story 1.1 - Natural Language CLI Interface
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class CommandIntent(Enum):
    """Types of command intents"""
    ANALYZE = "analyze"
    SCAN = "scan"
    DEPLOY = "deploy"
    TEST = "test"
    BUILD = "build"
    OPTIMIZE = "optimize"
    DOCUMENT = "document"
    SEARCH = "search"
    EXPLAIN = "explain"
    FIX = "fix"
    UNKNOWN = "unknown"

@dataclass
class ParsedCommand:
    """Parsed natural language command"""
    intent: CommandIntent
    target: Optional[str]
    parameters: Dict[str, Any]
    confidence: float
    original_text: str
    suggested_agent: Optional[str]

class NaturalLanguageParser:
    """Parse natural language commands into structured actions"""
    
    def __init__(self):
        # Intent patterns
        self.intent_patterns = {
            CommandIntent.ANALYZE: [
                r"analyze\s+(?:my\s+)?(\w+)",
                r"check\s+(?:the\s+)?(\w+)",
                r"review\s+(?:the\s+)?(\w+)",
                r"examine\s+(?:the\s+)?(\w+)"
            ],
            CommandIntent.SCAN: [
                r"scan\s+(?:for\s+)?(\w+)",
                r"find\s+(\w+)",
                r"detect\s+(\w+)",
                r"look\s+for\s+(\w+)"
            ],
            CommandIntent.DEPLOY: [
                r"deploy\s+(?:to\s+)?(\w+)",
                r"release\s+(?:to\s+)?(\w+)",
                r"push\s+(?:to\s+)?(\w+)"
            ],
            CommandIntent.TEST: [
                r"test\s+(?:the\s+)?(\w+)",
                r"run\s+tests",
                r"validate\s+(\w+)",
                r"verify\s+(\w+)"
            ],
            CommandIntent.BUILD: [
                r"build\s+(?:the\s+)?(\w+)?",
                r"compile\s+(?:the\s+)?(\w+)?",
                r"create\s+(?:a\s+)?(\w+)"
            ],
            CommandIntent.OPTIMIZE: [
                r"optimize\s+(?:the\s+)?(\w+)",
                r"improve\s+(?:the\s+)?(\w+)",
                r"speed\s+up\s+(\w+)",
                r"make\s+(\w+)\s+faster"
            ],
            CommandIntent.DOCUMENT: [
                r"document\s+(?:the\s+)?(\w+)",
                r"write\s+docs\s+(?:for\s+)?(\w+)?",
                r"generate\s+documentation"
            ],
            CommandIntent.SEARCH: [
                r"search\s+for\s+(.+)",
                r"find\s+all\s+(.+)",
                r"where\s+is\s+(.+)",
                r"locate\s+(.+)"
            ],
            CommandIntent.EXPLAIN: [
                r"explain\s+(?:how\s+)?(.+)",
                r"what\s+(?:is|does)\s+(.+)",
                r"how\s+(?:does|to)\s+(.+)",
                r"why\s+(?:is|does)\s+(.+)"
            ],
            CommandIntent.FIX: [
                r"fix\s+(?:the\s+)?(.+)",
                r"repair\s+(?:the\s+)?(.+)",
                r"resolve\s+(?:the\s+)?(.+)",
                r"solve\s+(?:the\s+)?(.+)"
            ]
        }
        
        # Target type patterns
        self.target_patterns = {
            "codebase": ["codebase", "code", "project", "repository", "repo"],
            "architecture": ["architecture", "design", "structure", "patterns"],
            "security": ["security", "vulnerabilities", "vulns", "threats"],
            "performance": ["performance", "speed", "latency", "bottlenecks"],
            "duplicates": ["duplicates", "duplication", "redundancy", "copies"],
            "dependencies": ["dependencies", "deps", "packages", "libraries"],
            "tests": ["tests", "testing", "coverage", "unit tests"],
            "quality": ["quality", "bugs", "issues", "problems"],
            "database": ["database", "db", "queries", "schema"],
            "api": ["api", "endpoints", "routes", "services"]
        }
        
        # Agent mapping
        self.agent_mapping = {
            "duplicates": "scout",
            "architecture": "architect",
            "security": "guardian",
            "performance": "optimizer",
            "tests": "tester",
            "documentation": "documenter",
            "database": "dba",
            "api": "api_analyzer"
        }
    
    def parse(self, command: str) -> ParsedCommand:
        """Parse natural language command"""
        command = command.lower().strip()
        
        # Detect intent
        intent, target, confidence = self._detect_intent(command)
        
        # Extract parameters
        parameters = self._extract_parameters(command, intent)
        
        # Suggest agent
        agent = self._suggest_agent(intent, target, parameters)
        
        return ParsedCommand(
            intent=intent,
            target=target,
            parameters=parameters,
            confidence=confidence,
            original_text=command,
            suggested_agent=agent
        )
    
    def _detect_intent(self, command: str) -> Tuple[CommandIntent, Optional[str], float]:
        """Detect command intent and target"""
        best_match = (CommandIntent.UNKNOWN, None, 0.0)
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    # Calculate confidence based on pattern match
                    confidence = self._calculate_confidence(command, pattern, match)
                    
                    if confidence > best_match[2]:
                        target = match.group(1) if len(match.groups()) > 0 else None
                        best_match = (intent, target, confidence)
        
        return best_match
    
    def _calculate_confidence(
        self,
        command: str,
        pattern: str,
        match: re.Match
    ) -> float:
        """Calculate confidence score for intent detection"""
        # Base confidence from match
        confidence = 0.5
        
        # Increase confidence if match is at the beginning
        if match.start() == 0:
            confidence += 0.2
        
        # Increase confidence based on match coverage
        coverage = len(match.group()) / len(command)
        confidence += coverage * 0.3
        
        return min(confidence, 1.0)
    
    def _extract_parameters(
        self,
        command: str,
        intent: CommandIntent
    ) -> Dict[str, Any]:
        """Extract parameters from command"""
        parameters = {}
        
        # Extract common parameters
        if "verbose" in command or "detailed" in command:
            parameters["verbose"] = True
        
        if "quick" in command or "fast" in command:
            parameters["quick"] = True
        
        if "comprehensive" in command or "thorough" in command:
            parameters["comprehensive"] = True
        
        # Extract file patterns
        file_pattern = re.search(r'(?:in|for)\s+([*\w./]+)', command)
        if file_pattern:
            parameters["file_pattern"] = file_pattern.group(1)
        
        # Extract depth/level
        depth_match = re.search(r'(?:depth|level)\s+(\d+)', command)
        if depth_match:
            parameters["depth"] = int(depth_match.group(1))
        
        # Extract environment for deployment
        if intent == CommandIntent.DEPLOY:
            for env in ["production", "staging", "development", "dev", "prod"]:
                if env in command:
                    parameters["environment"] = env
                    break
        
        # Extract analysis types
        if intent == CommandIntent.ANALYZE:
            analysis_types = []
            for analysis_type in ["scaling", "security", "quality", "performance"]:
                if analysis_type in command:
                    analysis_types.append(analysis_type)
            
            if analysis_types:
                parameters["analysis_types"] = analysis_types
        
        return parameters
    
    def _suggest_agent(
        self,
        intent: CommandIntent,
        target: Optional[str],
        parameters: Dict[str, Any]
    ) -> Optional[str]:
        """Suggest appropriate agent for the command"""
        # Check target-based mapping
        if target:
            for key, agent in self.agent_mapping.items():
                if key in target:
                    return agent
        
        # Check parameters for hints
        if "analysis_types" in parameters:
            for analysis_type in parameters["analysis_types"]:
                if analysis_type in self.agent_mapping:
                    return self.agent_mapping[analysis_type]
        
        # Intent-based defaults
        intent_defaults = {
            CommandIntent.ANALYZE: "architect",
            CommandIntent.SCAN: "scout",
            CommandIntent.DEPLOY: "deployer",
            CommandIntent.TEST: "tester",
            CommandIntent.OPTIMIZE: "optimizer",
            CommandIntent.DOCUMENT: "documenter",
            CommandIntent.SEARCH: "scout",
            CommandIntent.FIX: "fixer"
        }
        
        return intent_defaults.get(intent)

class CommandRouter:
    """Route parsed commands to appropriate agents"""
    
    def __init__(self):
        self.agent_registry = {}
        self.execution_history = []
    
    def register_agent(self, name: str, agent_class):
        """Register an agent for command routing"""
        self.agent_registry[name] = agent_class
        logger.debug(f"Registered agent: {name}")
    
    async def route_command(
        self,
        parsed_command: ParsedCommand
    ) -> Dict[str, Any]:
        """Route command to appropriate agent"""
        # Get suggested agent
        agent_name = parsed_command.suggested_agent
        
        if not agent_name or agent_name not in self.agent_registry:
            return {
                "error": f"No suitable agent found for command",
                "suggestion": self._suggest_alternative(parsed_command)
            }
        
        # Get agent class
        agent_class = self.agent_registry[agent_name]
        
        try:
            # Instantiate and execute
            agent = agent_class()
            result = await self._execute_agent(
                agent,
                parsed_command.intent,
                parsed_command.parameters
            )
            
            # Record execution
            self.execution_history.append({
                "command": parsed_command.original_text,
                "agent": agent_name,
                "intent": parsed_command.intent.value,
                "success": True
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing agent {agent_name}: {e}")
            
            self.execution_history.append({
                "command": parsed_command.original_text,
                "agent": agent_name,
                "intent": parsed_command.intent.value,
                "success": False,
                "error": str(e)
            })
            
            return {
                "error": f"Failed to execute command: {str(e)}",
                "agent": agent_name
            }
    
    async def _execute_agent(
        self,
        agent,
        intent: CommandIntent,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with intent and parameters"""
        # Map intent to agent method
        method_mapping = {
            CommandIntent.ANALYZE: "analyze",
            CommandIntent.SCAN: "scan",
            CommandIntent.DEPLOY: "deploy",
            CommandIntent.TEST: "test",
            CommandIntent.BUILD: "build",
            CommandIntent.OPTIMIZE: "optimize",
            CommandIntent.DOCUMENT: "document",
            CommandIntent.SEARCH: "search",
            CommandIntent.EXPLAIN: "explain",
            CommandIntent.FIX: "fix"
        }
        
        method_name = method_mapping.get(intent, "execute")
        
        if hasattr(agent, method_name):
            method = getattr(agent, method_name)
            return await method(**parameters)
        else:
            # Fallback to generic execute
            if hasattr(agent, "execute"):
                return await agent.execute(intent=intent.value, **parameters)
            else:
                raise AttributeError(f"Agent has no suitable method for {intent.value}")
    
    def _suggest_alternative(
        self,
        parsed_command: ParsedCommand
    ) -> str:
        """Suggest alternative command or agent"""
        suggestions = []
        
        if parsed_command.intent == CommandIntent.UNKNOWN:
            suggestions.append("Try being more specific with your command")
            suggestions.append("Available commands: analyze, scan, deploy, test, optimize, document")
        else:
            suggestions.append(f"The '{parsed_command.intent.value}' command needs a valid target")
            suggestions.append("Available agents: " + ", ".join(self.agent_registry.keys()))
        
        return "; ".join(suggestions)

class InteractiveCLI:
    """Interactive CLI with natural language support"""
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.router = CommandRouter()
        self.session_context = {}
        self.command_history = []
    
    async def process_command(self, command: str) -> Dict[str, Any]:
        """Process a natural language command"""
        # Add to history
        self.command_history.append(command)
        
        # Parse command
        parsed = self.parser.parse(command)
        
        # Show interpretation if low confidence
        if parsed.confidence < 0.7:
            confirmation = await self._confirm_interpretation(parsed)
            if not confirmation:
                return await self._get_clarification(command)
        
        # Route to agent
        result = await self.router.route_command(parsed)
        
        # Update session context
        self._update_context(parsed, result)
        
        return {
            "command": command,
            "interpretation": {
                "intent": parsed.intent.value,
                "target": parsed.target,
                "parameters": parsed.parameters,
                "confidence": parsed.confidence,
                "agent": parsed.suggested_agent
            },
            "result": result
        }
    
    async def _confirm_interpretation(
        self,
        parsed: ParsedCommand
    ) -> bool:
        """Confirm command interpretation with user"""
        print(f"\nI understood: {parsed.intent.value}")
        if parsed.target:
            print(f"Target: {parsed.target}")
        if parsed.parameters:
            print(f"Parameters: {parsed.parameters}")
        print(f"Confidence: {parsed.confidence:.1%}")
        
        response = input("Is this correct? (y/n): ")
        return response.lower() == 'y'
    
    async def _get_clarification(self, command: str) -> Dict[str, Any]:
        """Get clarification for ambiguous command"""
        print("\nI'm not sure what you want to do.")
        print("Here are some examples:")
        print("  - 'analyze my codebase for duplicates'")
        print("  - 'scan for security vulnerabilities'")
        print("  - 'optimize database queries'")
        print("  - 'test the API endpoints'")
        
        new_command = input("\nPlease rephrase your command: ")
        
        if new_command:
            return await self.process_command(new_command)
        else:
            return {"error": "Command cancelled"}
    
    def _update_context(
        self,
        parsed: ParsedCommand,
        result: Dict[str, Any]
    ):
        """Update session context with command results"""
        self.session_context["last_command"] = parsed.original_text
        self.session_context["last_intent"] = parsed.intent.value
        self.session_context["last_agent"] = parsed.suggested_agent
        
        if "data" in result:
            self.session_context["last_result"] = result["data"]
    
    def get_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions for autocomplete"""
        suggestions = []
        
        # Common command starters
        starters = [
            "analyze", "scan", "deploy", "test", "build",
            "optimize", "document", "search", "explain", "fix"
        ]
        
        for starter in starters:
            if starter.startswith(partial_command.lower()):
                # Add common completions
                suggestions.append(f"{starter} my codebase")
                suggestions.append(f"{starter} for issues")
                suggestions.append(f"{starter} the architecture")
        
        # Add history-based suggestions
        for cmd in self.command_history[-10:]:
            if cmd.startswith(partial_command):
                suggestions.append(cmd)
        
        return list(set(suggestions))[:10]  # Return unique suggestions

# Example usage
async def example_usage():
    """Example of using the natural language CLI"""
    cli = InteractiveCLI()
    
    # Register mock agents
    class MockScoutAgent:
        async def scan(self, **kwargs):
            return {"found": 5, "duplicates": ["file1.py", "file2.py"]}
    
    class MockArchitectAgent:
        async def analyze(self, **kwargs):
            return {"patterns": ["MVC", "Repository"], "issues": []}
    
    cli.router.register_agent("scout", MockScoutAgent)
    cli.router.register_agent("architect", MockArchitectAgent)
    
    # Process commands
    commands = [
        "analyze my codebase for duplicates",
        "scan for security vulnerabilities quickly",
        "check the architecture patterns in src/",
        "find all duplicate code"
    ]
    
    for cmd in commands:
        print(f"\nCommand: {cmd}")
        result = await cli.process_command(cmd)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())