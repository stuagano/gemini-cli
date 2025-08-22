"""
Unified Agent Base Class
Merges BMAD agent structure with Gemini Enterprise Architect capabilities
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for a unified agent"""
    id: str
    name: str
    title: str
    icon: str
    when_to_use: str
    persona: Dict[str, Any]
    commands: List[Dict[str, str]]
    dependencies: Dict[str, List[str]]
    customization: Optional[Dict[str, Any]] = None


class TeachingEngine:
    """Progressive teaching system for developers"""
    
    def __init__(self, developer_level: str = "intermediate"):
        self.level = developer_level
        self.learning_history = []
        
    def teach(self, concept: str, context: Dict[str, Any]) -> str:
        """Generate teaching content based on developer level"""
        if self.level == "junior":
            return self._detailed_explanation(concept, context)
        elif self.level == "senior":
            return self._quick_validation(concept, context)
        else:  # architect
            return self._strategic_discussion(concept, context)
    
    def _detailed_explanation(self, concept: str, context: Dict[str, Any]) -> str:
        """Detailed explanation for junior developers"""
        return f"""
        📚 Learning Moment: {concept}
        
        What: {context.get('what', 'Understanding the concept')}
        Why: {context.get('why', 'This is important because...')}
        How: {context.get('how', 'Step-by-step implementation')}
        Example: {context.get('example', 'Here\'s a practical example')}
        """
    
    def _quick_validation(self, concept: str, context: Dict[str, Any]) -> str:
        """Quick validation for senior developers"""
        return f"✓ {concept}: {context.get('key_point', 'Best practice applied')}"
    
    def _strategic_discussion(self, concept: str, context: Dict[str, Any]) -> str:
        """Strategic discussion for architects"""
        return f"🏗️ Architecture Decision: {concept} - Trade-offs: {context.get('tradeoffs', 'Consider...')}"
    
    def capture_learning(self, task: str, result: Any):
        """Capture learning moments for future reference"""
        self.learning_history.append({
            'task': task,
            'result': result,
            'timestamp': self._get_timestamp()
        })
        
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


class StandardsEnforcer:
    """Enforce enterprise standards and best practices"""
    
    def __init__(self, standards_config: Optional[Dict[str, Any]] = None):
        self.standards = standards_config or self._load_default_standards()
        
    def _load_default_standards(self) -> Dict[str, Any]:
        """Load default enterprise standards"""
        return {
            'scaling': {
                'max_unbounded_queries': 0,
                'pagination_required': True,
                'caching_required': True,
                'rate_limiting_required': True
            },
            'security': {
                'authentication_required': True,
                'encryption_required': True,
                'secrets_in_code': False
            },
            'code_quality': {
                'test_coverage_min': 80,
                'documentation_required': True,
                'type_hints_required': True
            }
        }
    
    def check(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check task against standards and return violations"""
        violations = []
        
        # Check scaling standards
        if task.get('type') == 'api_endpoint':
            if not task.get('pagination'):
                violations.append({
                    'type': 'scaling',
                    'severity': 'critical',
                    'message': 'API endpoint missing pagination',
                    'fix': 'Implement cursor-based pagination'
                })
                
        # Check security standards
        if task.get('handles_user_data'):
            if not task.get('authentication'):
                violations.append({
                    'type': 'security',
                    'severity': 'critical',
                    'message': 'User data endpoint missing authentication',
                    'fix': 'Add authentication middleware'
                })
                
        return violations


class ServiceAdvisor:
    """Advise on GCP service selection"""
    
    def __init__(self):
        self.decision_trees = self._load_decision_trees()
        
    def _load_decision_trees(self) -> Dict[str, Any]:
        """Load service selection decision trees"""
        return {
            'compute': {
                'stateless_http': 'cloud_run',
                'stateful': 'gke',
                'batch': 'cloud_batch',
                'legacy': 'gce'
            },
            'data': {
                'document': 'firestore',
                'relational': 'cloud_sql',
                'global_relational': 'spanner',
                'analytics': 'bigquery',
                'time_series': 'bigtable'
            },
            'ml': {
                'automl': 'vertex_ai_automl',
                'custom': 'vertex_ai_custom',
                'inference': 'vertex_ai_endpoints'
            }
        }
    
    def recommend(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend services based on requirements"""
        recommendations = {}
        
        # Analyze compute needs
        if requirements.get('compute'):
            compute_type = self._analyze_compute_type(requirements['compute'])
            recommendations['compute'] = {
                'service': self.decision_trees['compute'].get(compute_type),
                'reason': f'Best fit for {compute_type} workloads'
            }
            
        # Analyze data needs
        if requirements.get('data'):
            data_type = self._analyze_data_type(requirements['data'])
            recommendations['data'] = {
                'service': self.decision_trees['data'].get(data_type),
                'reason': f'Optimal for {data_type} data patterns'
            }
            
        return recommendations
    
    def _analyze_compute_type(self, compute_req: Dict[str, Any]) -> str:
        """Analyze compute requirements to determine type"""
        if compute_req.get('stateless') and compute_req.get('http'):
            return 'stateless_http'
        elif compute_req.get('stateful'):
            return 'stateful'
        elif compute_req.get('batch_processing'):
            return 'batch'
        else:
            return 'legacy'
            
    def _analyze_data_type(self, data_req: Dict[str, Any]) -> str:
        """Analyze data requirements to determine type"""
        if data_req.get('document_model'):
            return 'document'
        elif data_req.get('global_consistency'):
            return 'global_relational'
        elif data_req.get('analytics'):
            return 'analytics'
        elif data_req.get('time_series'):
            return 'time_series'
        else:
            return 'relational'


class DependencyMapper:
    """Map and track code dependencies"""
    
    def __init__(self):
        self.dependency_graph = {}
        
    def analyze(self, codebase_path: str) -> Dict[str, Any]:
        """Analyze codebase for dependencies"""
        # This would integrate with Scout agent functionality
        return {
            'classes': self._scan_classes(codebase_path),
            'methods': self._scan_methods(codebase_path),
            'imports': self._scan_imports(codebase_path),
            'critical_paths': self._identify_critical_paths()
        }
    
    def _scan_classes(self, path: str) -> List[str]:
        """Scan for class definitions"""
        # Implementation would scan actual code
        return []
    
    def _scan_methods(self, path: str) -> List[str]:
        """Scan for method definitions"""
        # Implementation would scan actual code
        return []
    
    def _scan_imports(self, path: str) -> List[str]:
        """Scan for import statements"""
        # Implementation would scan actual code
        return []
    
    def _identify_critical_paths(self) -> List[str]:
        """Identify critical dependency paths"""
        # Implementation would analyze dependency graph
        return []


class UnifiedAgent(ABC):
    """
    Base class for all agents in the unified BMAD + Gemini system
    Combines BMAD agent structure with Gemini Enterprise Architect capabilities
    """
    
    def __init__(self, agent_config: AgentConfig, developer_level: str = "intermediate"):
        # BMAD configuration
        self.config = agent_config
        self.persona = agent_config.persona
        self.commands = agent_config.commands
        self.dependencies = agent_config.dependencies
        
        # Gemini Enterprise Architect components
        self.teaching_engine = TeachingEngine(developer_level)
        self.standards_enforcer = StandardsEnforcer()
        self.service_advisor = ServiceAdvisor()
        self.dependency_mapper = DependencyMapper()
        
        # State management
        self.current_context = {}
        self.artifacts = {}
        
    def execute_with_teaching(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with teaching and standards enforcement"""
        
        # Pre-execution: Check standards
        violations = self.standards_enforcer.check({'type': task, **context})
        if violations:
            self.teach_and_correct(violations, context)
            
        # Execution: Run the task
        result = self.execute_task(task, context)
        
        # Post-execution: Capture learning
        self.teaching_engine.capture_learning(task, result)
        
        # Generate recommendations if applicable
        if context.get('needs_recommendations'):
            result['recommendations'] = self.service_advisor.recommend(context)
            
        return result
    
    def teach_and_correct(self, violations: List[Dict[str, Any]], context: Dict[str, Any]):
        """Teach about violations and provide corrections"""
        for violation in violations:
            teaching_context = {
                'what': violation['message'],
                'why': f"This violates {violation['type']} standards",
                'how': violation['fix'],
                'example': self._get_example_for_violation(violation)
            }
            
            teaching = self.teaching_engine.teach(
                f"{violation['type'].title()} Issue Detected",
                teaching_context
            )
            
            print(teaching)
            
    def _get_example_for_violation(self, violation: Dict[str, Any]) -> str:
        """Get example fix for a violation"""
        examples = {
            'scaling': """
            # Before (will fail at scale):
            @app.get("/users")
            def get_users():
                return db.query("SELECT * FROM users")
            
            # After (handles millions of users):
            @app.get("/users")
            def get_users(cursor: str = None, limit: int = 100):
                query = users_table.select().limit(limit)
                if cursor:
                    query = query.where(users_table.c.id > cursor)
                return paginate(query)
            """,
            'security': """
            # Add authentication:
            from fastapi import Depends, HTTPException
            from .auth import get_current_user
            
            @app.get("/users")
            def get_users(current_user: User = Depends(get_current_user)):
                if not current_user:
                    raise HTTPException(401)
                return get_user_data()
            """
        }
        return examples.get(violation['type'], "See documentation for examples")
    
    @abstractmethod
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual task - must be implemented by each agent"""
        pass
    
    def load_bmad_template(self, template_name: str) -> Dict[str, Any]:
        """Load a BMAD template from the templates directory"""
        template_path = Path(f".bmad-core/templates/{template_name}")
        if template_path.exists():
            with open(template_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def load_bmad_task(self, task_name: str) -> str:
        """Load a BMAD task from the tasks directory"""
        task_path = Path(f".bmad-core/tasks/{task_name}")
        if task_path.exists():
            with open(task_path, 'r') as f:
                return f.read()
        return ""
    
    def challenge_decision(self, decision: str, context: Dict[str, Any]) -> Optional[str]:
        """Challenge a decision if it violates best practices"""
        # Check if decision follows best practices
        if self._violates_best_practices(decision, context):
            return self._generate_challenge(decision, context)
        return None
    
    def _violates_best_practices(self, decision: str, context: Dict[str, Any]) -> bool:
        """Check if a decision violates best practices"""
        # Implementation would check against knowledge base
        return False
    
    def _generate_challenge(self, decision: str, context: Dict[str, Any]) -> str:
        """Generate a constructive challenge with evidence"""
        return f"""
        🤔 I need to challenge this decision:
        
        Decision: {decision}
        
        Concern: This may lead to scaling/security/maintenance issues
        
        Evidence: Based on similar implementations, this approach has failed at scale
        
        Alternative: Consider [specific alternative] which has proven successful
        
        Would you like to:
        1. Proceed with awareness of risks
        2. Explore the alternative approach
        3. Discuss the trade-offs
        """
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent': self.config.name,
            'context': self.current_context,
            'artifacts': list(self.artifacts.keys()),
            'learning_events': len(self.teaching_engine.learning_history)
        }