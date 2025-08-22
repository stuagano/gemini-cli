"""
Scout-First Architecture
Scout analyzes codebase before any changes to prevent duplicate code
Epic 1: Story 1.2 - Scout-First Architecture
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysis:
    """Result from Scout analysis"""
    file_path: str
    function_signatures: List[str]
    class_definitions: List[str]
    imports: List[str]
    dependencies: List[str]
    complexity_score: float
    loc: int  # Lines of code
    duplicates: List[str]
    potential_issues: List[str]
    timestamp: datetime

@dataclass
class ArchitectureDecision:
    """Decision made by Scout before code generation"""
    decision: str
    rationale: str
    existing_alternatives: List[str]
    recommended_approach: str
    risk_level: str
    impact: str

class ScoutFirstOrchestrator:
    """Orchestrator that ensures Scout runs before any code changes"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.decision_history = []
        self.scout_enabled = True
        self.bypass_patterns = []  # Patterns that can bypass Scout
        
        # Performance tracking
        self.metrics = {
            'analyses_run': 0,
            'duplicates_prevented': 0,
            'decisions_made': 0,
            'bypasses_allowed': 0,
            'time_saved_hours': 0
        }
    
    async def analyze_before_action(
        self,
        action_type: str,
        target_path: str,
        proposed_changes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run Scout analysis before any code action"""
        logger.info(f"Scout-first analysis for {action_type} on {target_path}")
        
        # Check if Scout should be bypassed
        if self._should_bypass(action_type, target_path):
            self.metrics['bypasses_allowed'] += 1
            return {
                "scout_bypassed": True,
                "reason": "Matches bypass pattern",
                "action_approved": True
            }
        
        if not self.scout_enabled:
            return {
                "scout_disabled": True,
                "action_approved": True
            }
        
        # Run comprehensive Scout analysis
        analysis = await self._run_scout_analysis(target_path, proposed_changes)
        
        # Make architecture decision
        decision = await self._make_architecture_decision(
            action_type,
            analysis,
            proposed_changes
        )
        
        # Update metrics
        self.metrics['analyses_run'] += 1
        self.metrics['decisions_made'] += 1
        
        if len(analysis.duplicates) > 0:
            self.metrics['duplicates_prevented'] += len(analysis.duplicates)
        
        # Store decision in history
        self.decision_history.append(decision)
        
        # Determine if action should proceed
        action_approved = self._evaluate_action_approval(decision, analysis)
        
        return {
            "scout_analysis": analysis,
            "architecture_decision": decision,
            "action_approved": action_approved,
            "recommendations": self._generate_recommendations(analysis, decision),
            "alternatives": decision.existing_alternatives,
            "estimated_time_saved_hours": self._estimate_time_saved(analysis)
        }
    
    async def _run_scout_analysis(
        self,
        target_path: str,
        proposed_changes: Optional[Dict[str, Any]] = None
    ) -> CodeAnalysis:
        """Run comprehensive Scout analysis"""
        # Check cache first
        cache_key = self._generate_cache_key(target_path, proposed_changes)
        
        if cache_key in self.analysis_cache:
            cached_analysis = self.analysis_cache[cache_key]
            # Check if cache is still valid (less than 1 hour old)
            if (datetime.now() - cached_analysis.timestamp).seconds < 3600:
                logger.debug("Using cached Scout analysis")
                return cached_analysis
        
        # Analyze existing codebase
        existing_analysis = await self._analyze_existing_code(target_path)
        
        # Analyze proposed changes if provided
        if proposed_changes:
            proposed_analysis = await self._analyze_proposed_changes(
                proposed_changes,
                existing_analysis
            )
        else:
            proposed_analysis = existing_analysis
        
        # Cache the analysis
        self.analysis_cache[cache_key] = proposed_analysis
        
        return proposed_analysis
    
    async def _analyze_existing_code(self, target_path: str) -> CodeAnalysis:
        """Analyze existing codebase"""
        path = Path(target_path)
        
        if path.is_file():
            # Analyze single file
            return await self._analyze_file(path)
        elif path.is_dir():
            # Analyze directory
            return await self._analyze_directory(path)
        else:
            # Analyze entire project
            return await self._analyze_project()
    
    async def _analyze_file(self, file_path: Path) -> CodeAnalysis:
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return self._empty_analysis(str(file_path))
        
        # Extract information from file
        function_signatures = self._extract_functions(content)
        class_definitions = self._extract_classes(content)
        imports = self._extract_imports(content)
        dependencies = self._extract_dependencies(content)
        complexity_score = self._calculate_complexity(content)
        loc = len([line for line in content.split('\n') if line.strip()])
        
        # Find duplicates
        duplicates = await self._find_duplicates(content, function_signatures)
        
        # Identify potential issues
        potential_issues = self._identify_issues(content, function_signatures, class_definitions)
        
        return CodeAnalysis(
            file_path=str(file_path),
            function_signatures=function_signatures,
            class_definitions=class_definitions,
            imports=imports,
            dependencies=dependencies,
            complexity_score=complexity_score,
            loc=loc,
            duplicates=duplicates,
            potential_issues=potential_issues,
            timestamp=datetime.now()
        )
    
    async def _analyze_directory(self, dir_path: Path) -> CodeAnalysis:
        """Analyze all files in directory"""
        analyses = []
        
        # Find all code files
        for file_path in dir_path.rglob("*.py"):
            analysis = await self._analyze_file(file_path)
            analyses.append(analysis)
        
        # Aggregate results
        return self._aggregate_analyses(analyses)
    
    async def _analyze_project(self) -> CodeAnalysis:
        """Analyze entire project"""
        project_root = Path.cwd()
        return await self._analyze_directory(project_root)
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function signatures from code"""
        import re
        
        # Python function pattern
        pattern = r'def\s+(\w+)\s*\([^)]*\):'
        matches = re.findall(pattern, content)
        
        return matches
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class definitions from code"""
        import re
        
        # Python class pattern
        pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        matches = re.findall(pattern, content)
        
        return matches
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        import re
        
        # Import patterns
        patterns = [
            r'import\s+([\w.]+)',
            r'from\s+([\w.]+)\s+import'
        ]
        
        imports = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract external dependencies"""
        imports = self._extract_imports(content)
        
        # Filter for external packages (not standard library)
        external_deps = []
        stdlib_modules = {'os', 'sys', 're', 'json', 'time', 'datetime', 'asyncio'}
        
        for imp in imports:
            root_module = imp.split('.')[0]
            if root_module not in stdlib_modules:
                external_deps.append(root_module)
        
        return list(set(external_deps))
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate cyclomatic complexity (simplified)"""
        complexity_keywords = [
            'if', 'elif', 'else', 'for', 'while', 'try', 'except',
            'finally', 'with', 'and', 'or'
        ]
        
        complexity = 1  # Base complexity
        for keyword in complexity_keywords:
            complexity += content.lower().count(keyword)
        
        # Normalize by lines of code
        loc = len([line for line in content.split('\n') if line.strip()])
        if loc > 0:
            return complexity / loc * 100
        
        return 0
    
    async def _find_duplicates(
        self,
        content: str,
        functions: List[str]
    ) -> List[str]:
        """Find duplicate code patterns"""
        duplicates = []
        
        # Check for duplicate function names in the project
        for func_name in functions:
            similar_functions = await self._find_similar_functions(func_name)
            if len(similar_functions) > 1:
                duplicates.append(f"Similar to: {', '.join(similar_functions)}")
        
        # Check for duplicate code blocks (simplified)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if len(line.strip()) > 20:  # Ignore short lines
                similar_lines = await self._find_similar_code_blocks(line.strip())
                if len(similar_lines) > 1:
                    duplicates.append(f"Line {i+1}: duplicate pattern found")
        
        return list(set(duplicates))
    
    async def _find_similar_functions(self, func_name: str) -> List[str]:
        """Find functions with similar names or signatures"""
        # Mock implementation - in production, this would search the codebase
        similar = [func_name]
        
        # Add mock similar functions for demonstration
        if 'process' in func_name.lower():
            similar.append('handle_process')
        if 'get' in func_name.lower():
            similar.append('retrieve_data')
        
        return similar
    
    async def _find_similar_code_blocks(self, code_block: str) -> List[str]:
        """Find similar code blocks"""
        # Mock implementation - in production, this would use AST comparison
        return [code_block]  # Simplified
    
    def _identify_issues(
        self,
        content: str,
        functions: List[str],
        classes: List[str]
    ) -> List[str]:
        """Identify potential code issues"""
        issues = []
        
        # Check for common issues
        if len(functions) > 20:
            issues.append("File has too many functions (>20)")
        
        if len(classes) > 5:
            issues.append("File has too many classes (>5)")
        
        # Check for long lines
        lines = content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            issues.append(f"Long lines found: {long_lines[:5]}")  # Show first 5
        
        # Check for TODO/FIXME comments
        if 'TODO' in content.upper():
            issues.append("Contains TODO comments")
        
        if 'FIXME' in content.upper():
            issues.append("Contains FIXME comments")
        
        # Check for hardcoded values
        import re
        if re.search(r'["\'][^"\']*(?:localhost|127\.0\.0\.1|password|secret)[^"\']*["\']', content):
            issues.append("Contains potential hardcoded values")
        
        return issues
    
    async def _analyze_proposed_changes(
        self,
        proposed_changes: Dict[str, Any],
        existing_analysis: CodeAnalysis
    ) -> CodeAnalysis:
        """Analyze proposed changes against existing code"""
        # For now, return existing analysis
        # In production, this would analyze the proposed changes
        return existing_analysis
    
    def _aggregate_analyses(self, analyses: List[CodeAnalysis]) -> CodeAnalysis:
        """Aggregate multiple analyses into one"""
        if not analyses:
            return self._empty_analysis(".")
        
        # Aggregate data
        all_functions = []
        all_classes = []
        all_imports = []
        all_dependencies = []
        all_duplicates = []
        all_issues = []
        total_complexity = 0
        total_loc = 0
        
        for analysis in analyses:
            all_functions.extend(analysis.function_signatures)
            all_classes.extend(analysis.class_definitions)
            all_imports.extend(analysis.imports)
            all_dependencies.extend(analysis.dependencies)
            all_duplicates.extend(analysis.duplicates)
            all_issues.extend(analysis.potential_issues)
            total_complexity += analysis.complexity_score
            total_loc += analysis.loc
        
        avg_complexity = total_complexity / len(analyses) if analyses else 0
        
        return CodeAnalysis(
            file_path="aggregated",
            function_signatures=list(set(all_functions)),
            class_definitions=list(set(all_classes)),
            imports=list(set(all_imports)),
            dependencies=list(set(all_dependencies)),
            complexity_score=avg_complexity,
            loc=total_loc,
            duplicates=list(set(all_duplicates)),
            potential_issues=list(set(all_issues)),
            timestamp=datetime.now()
        )
    
    def _empty_analysis(self, path: str) -> CodeAnalysis:
        """Return empty analysis"""
        return CodeAnalysis(
            file_path=path,
            function_signatures=[],
            class_definitions=[],
            imports=[],
            dependencies=[],
            complexity_score=0,
            loc=0,
            duplicates=[],
            potential_issues=[],
            timestamp=datetime.now()
        )
    
    async def _make_architecture_decision(
        self,
        action_type: str,
        analysis: CodeAnalysis,
        proposed_changes: Optional[Dict[str, Any]] = None
    ) -> ArchitectureDecision:
        """Make architecture decision based on analysis"""
        
        # Determine risk level
        risk_level = self._assess_risk_level(analysis)
        
        # Find existing alternatives
        alternatives = self._find_alternatives(analysis, action_type)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            action_type,
            analysis,
            alternatives,
            risk_level
        )
        
        decision = f"Proceed with {action_type}"
        rationale = self._generate_rationale(analysis, risk_level, alternatives)
        
        # Override decision if high risk
        if risk_level == "HIGH" and len(analysis.duplicates) > 5:
            decision = f"Refactor existing code before {action_type}"
            rationale += " High duplication detected - recommend consolidation first."
        
        return ArchitectureDecision(
            decision=decision,
            rationale=rationale,
            existing_alternatives=alternatives,
            recommended_approach=recommendation,
            risk_level=risk_level,
            impact=self._assess_impact(analysis, action_type)
        )
    
    def _assess_risk_level(self, analysis: CodeAnalysis) -> str:
        """Assess risk level of proposed changes"""
        risk_score = 0
        
        # Complexity risk
        if analysis.complexity_score > 15:
            risk_score += 2
        elif analysis.complexity_score > 10:
            risk_score += 1
        
        # Duplication risk
        if len(analysis.duplicates) > 5:
            risk_score += 3
        elif len(analysis.duplicates) > 2:
            risk_score += 1
        
        # Issue risk
        if len(analysis.potential_issues) > 10:
            risk_score += 2
        elif len(analysis.potential_issues) > 5:
            risk_score += 1
        
        # Dependencies risk
        if len(analysis.dependencies) > 20:
            risk_score += 1
        
        if risk_score >= 5:
            return "HIGH"
        elif risk_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _find_alternatives(
        self,
        analysis: CodeAnalysis,
        action_type: str
    ) -> List[str]:
        """Find existing alternatives to proposed action"""
        alternatives = []
        
        if action_type == "create_function":
            # Look for similar existing functions
            similar_functions = [f for f in analysis.function_signatures 
                               if any(keyword in f.lower() for keyword in ['process', 'handle', 'get', 'set'])]
            alternatives.extend(similar_functions[:3])  # Top 3
        
        if action_type == "create_class":
            # Look for similar existing classes
            similar_classes = [c for c in analysis.class_definitions 
                             if any(keyword in c.lower() for keyword in ['manager', 'handler', 'service'])]
            alternatives.extend(similar_classes[:3])  # Top 3
        
        if action_type == "add_dependency":
            # Look for existing similar dependencies
            similar_deps = [d for d in analysis.dependencies 
                          if any(keyword in d.lower() for keyword in ['http', 'json', 'db', 'cache'])]
            alternatives.extend(similar_deps[:3])  # Top 3
        
        return alternatives
    
    def _generate_recommendation(
        self,
        action_type: str,
        analysis: CodeAnalysis,
        alternatives: List[str],
        risk_level: str
    ) -> str:
        """Generate recommendation based on analysis"""
        
        if risk_level == "HIGH":
            return f"Refactor existing code before {action_type}"
        
        if len(alternatives) > 0:
            return f"Consider using existing {alternatives[0]} instead of {action_type}"
        
        if analysis.complexity_score > 10:
            return f"Simplify design before {action_type}"
        
        return f"Proceed with {action_type} using best practices"
    
    def _generate_rationale(
        self,
        analysis: CodeAnalysis,
        risk_level: str,
        alternatives: List[str]
    ) -> str:
        """Generate rationale for decision"""
        rationale_parts = []
        
        rationale_parts.append(f"Analysis shows {len(analysis.function_signatures)} functions")
        rationale_parts.append(f"and {len(analysis.class_definitions)} classes")
        
        if analysis.duplicates:
            rationale_parts.append(f"Found {len(analysis.duplicates)} potential duplicates")
        
        if analysis.complexity_score > 10:
            rationale_parts.append(f"Complexity score of {analysis.complexity_score:.1f} is above recommended threshold")
        
        if alternatives:
            rationale_parts.append(f"Found {len(alternatives)} existing alternatives")
        
        rationale_parts.append(f"Risk level assessed as {risk_level}")
        
        return ". ".join(rationale_parts) + "."
    
    def _assess_impact(self, analysis: CodeAnalysis, action_type: str) -> str:
        """Assess impact of proposed action"""
        if len(analysis.duplicates) > 5:
            return "High impact - will increase technical debt"
        elif analysis.complexity_score > 15:
            return "Medium impact - may increase maintenance burden"
        else:
            return "Low impact - minimal effect on codebase"
    
    def _evaluate_action_approval(
        self,
        decision: ArchitectureDecision,
        analysis: CodeAnalysis
    ) -> bool:
        """Evaluate whether action should be approved"""
        # Block high-risk actions with many duplicates
        if decision.risk_level == "HIGH" and len(analysis.duplicates) > 10:
            return False
        
        # Block if complexity is extremely high
        if analysis.complexity_score > 25:
            return False
        
        # Allow most other actions
        return True
    
    def _generate_recommendations(
        self,
        analysis: CodeAnalysis,
        decision: ArchitectureDecision
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if analysis.duplicates:
            recommendations.append(f"Remove {len(analysis.duplicates)} duplicate patterns")
        
        if analysis.complexity_score > 15:
            recommendations.append("Refactor complex functions to reduce complexity")
        
        if len(analysis.function_signatures) > 20:
            recommendations.append("Consider splitting file - too many functions")
        
        if decision.existing_alternatives:
            recommendations.append(f"Consider reusing: {decision.existing_alternatives[0]}")
        
        if analysis.potential_issues:
            recommendations.append("Address identified code issues before proceeding")
        
        return recommendations
    
    def _estimate_time_saved(self, analysis: CodeAnalysis) -> float:
        """Estimate time saved by Scout analysis"""
        time_saved = 0
        
        # Time saved from avoiding duplicates (2 hours per duplicate)
        time_saved += len(analysis.duplicates) * 2
        
        # Time saved from identifying issues early (1 hour per issue)
        time_saved += len(analysis.potential_issues) * 1
        
        # Time saved from complexity warnings (0.5 hours)
        if analysis.complexity_score > 15:
            time_saved += 0.5
        
        self.metrics['time_saved_hours'] += time_saved
        return time_saved
    
    def _should_bypass(self, action_type: str, target_path: str) -> bool:
        """Check if Scout analysis should be bypassed"""
        for pattern in self.bypass_patterns:
            if pattern in target_path or pattern in action_type:
                return True
        
        # Bypass for test files
        if 'test_' in target_path or '_test.py' in target_path:
            return True
        
        return False
    
    def _generate_cache_key(
        self,
        target_path: str,
        proposed_changes: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for analysis"""
        key_data = f"{target_path}:{str(proposed_changes)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Scout orchestrator metrics"""
        return {
            **self.metrics,
            "decision_history_count": len(self.decision_history),
            "cache_size": len(self.analysis_cache)
        }
    
    def configure(
        self,
        enabled: bool = True,
        bypass_patterns: Optional[List[str]] = None
    ):
        """Configure Scout orchestrator"""
        self.scout_enabled = enabled
        
        if bypass_patterns:
            self.bypass_patterns = bypass_patterns
        
        logger.info(f"Scout orchestrator configured: enabled={enabled}")

# Integration with CLI
class ScoutFirstCLIIntegration:
    """Integration with natural language CLI"""
    
    def __init__(self, orchestrator: ScoutFirstOrchestrator):
        self.orchestrator = orchestrator
    
    async def pre_command_hook(
        self,
        command: str,
        parsed_intent: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Hook that runs before any CLI command execution"""
        
        # Determine if command involves code changes
        code_changing_intents = [
            "create", "generate", "build", "modify", 
            "add", "implement", "write"
        ]
        
        if not any(intent in parsed_intent.lower() for intent in code_changing_intents):
            return {"scout_required": False}
        
        # Determine target path
        target_path = parameters.get("file_pattern", ".")
        
        # Run Scout analysis
        result = await self.orchestrator.analyze_before_action(
            action_type=parsed_intent,
            target_path=target_path,
            proposed_changes=parameters
        )
        
        return {
            "scout_required": True,
            "scout_result": result
        }

# Global instance
scout_orchestrator = ScoutFirstOrchestrator()

# Example usage
async def example_usage():
    """Example of Scout-first architecture"""
    
    # Configure Scout
    scout_orchestrator.configure(
        enabled=True,
        bypass_patterns=["test_", "example_"]
    )
    
    # Simulate code action
    result = await scout_orchestrator.analyze_before_action(
        action_type="create_function",
        target_path="src/services/user_service.py",
        proposed_changes={
            "function_name": "get_user_data",
            "parameters": ["user_id"],
            "return_type": "dict"
        }
    )
    
    print("Scout Analysis Result:")
    print(f"Action Approved: {result['action_approved']}")
    print(f"Decision: {result['architecture_decision'].decision}")
    print(f"Risk Level: {result['architecture_decision'].risk_level}")
    print(f"Recommendations: {result['recommendations']}")
    
    # Get metrics
    metrics = scout_orchestrator.get_metrics()
    print(f"\nScout Metrics: {metrics}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())