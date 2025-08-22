"""
PM Agent Task Generator for Gemini Enterprise Architect
Generates comprehensive task lists with DORA metrics and value optimization
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

@dataclass
class ProjectTask:
    """Represents a project task with full PM metadata"""
    id: str
    title: str
    description: str
    category: str  # CLI, Testing, Deployment, Documentation, Integration
    priority: str  # P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
    effort_hours: int
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    technical_requirements: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    value_score: float = 0.0
    dora_impact: Dict[str, str] = field(default_factory=dict)
    assigned_agent: str = ""
    status: str = "pending"

class GeminiPMTaskGenerator:
    """PM-driven task generation for Gemini Enterprise Architect"""
    
    def __init__(self):
        self.tasks: List[ProjectTask] = []
        self.task_categories = {
            'cli_integration': 'CLI Integration',
            'testing': 'Testing & Validation',
            'deployment': 'Cloud Deployment',
            'documentation': 'Documentation',
            'monitoring': 'Monitoring & Observability',
            'security': 'Security & Compliance',
            'performance': 'Performance Optimization',
            'integration': 'System Integration'
        }
        
    def generate_comprehensive_tasks(self) -> List[ProjectTask]:
        """Generate comprehensive task list for remaining implementation"""
        
        # Phase 1: CLI Integration (Week 9)
        self._add_cli_integration_tasks()
        
        # Phase 2: Testing & Validation (Week 11)
        self._add_testing_tasks()
        
        # Phase 3: Cloud Deployment (Week 10)
        self._add_deployment_tasks()
        
        # Phase 4: Documentation & Training
        self._add_documentation_tasks()
        
        # Phase 5: Monitoring & Observability
        self._add_monitoring_tasks()
        
        # Phase 6: Security & Compliance
        self._add_security_tasks()
        
        # Phase 7: Performance Optimization
        self._add_performance_tasks()
        
        # Phase 8: Integration & Polish
        self._add_integration_tasks()
        
        # Calculate value scores and DORA impacts
        self._calculate_value_scores()
        self._assess_dora_impacts()
        
        # Sort by priority and dependencies
        self._optimize_task_ordering()
        
        return self.tasks
    
    def _add_cli_integration_tasks(self):
        """Add CLI integration tasks"""
        
        self.tasks.append(ProjectTask(
            id="CLI-001",
            title="Create main CLI entry point with agent orchestration",
            description="Implement the main CLI application that orchestrates all agents through the Nexus core",
            category=self.task_categories['cli_integration'],
            priority="P0",
            effort_hours=8,
            dependencies=[],
            acceptance_criteria=[
                "CLI accepts natural language commands",
                "Routes commands to appropriate agents",
                "Handles multi-agent workflows",
                "Provides real-time status updates"
            ],
            technical_requirements=[
                "Use Click or Typer for CLI framework",
                "Integrate with existing Nexus core",
                "Support async operations",
                "Implement proper error handling"
            ],
            risks=["Complex command parsing", "Agent coordination overhead"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="CLI-002",
            title="Implement interactive mode with teaching capabilities",
            description="Add interactive CLI mode that leverages the teaching engine for progressive learning",
            category=self.task_categories['cli_integration'],
            priority="P0",
            effort_hours=6,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "Interactive prompt with context retention",
                "Teaching mode selection (junior/senior/architect)",
                "Progressive disclosure of information",
                "Session history and replay"
            ],
            technical_requirements=[
                "Implement REPL loop",
                "Context management system",
                "Teaching engine integration",
                "Session persistence"
            ],
            risks=["UX complexity", "State management challenges"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="CLI-003",
            title="Add Scout-first workflow for all operations",
            description="Integrate Scout agent as the first responder for all CLI operations to prevent duplication",
            category=self.task_categories['cli_integration'],
            priority="P0",
            effort_hours=4,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "Scout analyzes codebase before any operation",
                "Duplication detection integrated into workflow",
                "Dependency impact analysis shown",
                "Technical debt warnings displayed"
            ],
            technical_requirements=[
                "Scout agent integration",
                "Async analysis pipeline",
                "Result caching mechanism",
                "Impact visualization"
            ],
            risks=["Performance impact", "Analysis accuracy"],
            assigned_agent="Scout"
        ))
        
        self.tasks.append(ProjectTask(
            id="CLI-004",
            title="Implement Guardian continuous validation",
            description="Add Guardian system that continuously validates changes during development",
            category=self.task_categories['cli_integration'],
            priority="P1",
            effort_hours=6,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "Real-time validation during code changes",
                "Breaking change detection",
                "Test coverage monitoring",
                "Performance regression alerts"
            ],
            technical_requirements=[
                "File watcher implementation",
                "Background validation threads",
                "Notification system",
                "Integration with QA agent"
            ],
            risks=["Resource consumption", "False positives"],
            assigned_agent="QA"
        ))
        
        self.tasks.append(ProjectTask(
            id="CLI-005",
            title="Create natural language command parser",
            description="Implement NLP-based command parser for intuitive interaction",
            category=self.task_categories['cli_integration'],
            priority="P1",
            effort_hours=8,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "Understands natural language requests",
                "Maps to agent capabilities",
                "Handles ambiguous commands",
                "Provides command suggestions"
            ],
            technical_requirements=[
                "NLP library integration",
                "Intent classification",
                "Entity extraction",
                "Command mapping logic"
            ],
            risks=["NLP accuracy", "Command ambiguity"],
            assigned_agent="Developer"
        ))
    
    def _add_testing_tasks(self):
        """Add testing and validation tasks"""
        
        self.tasks.append(ProjectTask(
            id="TEST-001",
            title="Create comprehensive unit test suite",
            description="Develop unit tests for all agent components and core functionality",
            category=self.task_categories['testing'],
            priority="P0",
            effort_hours=12,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "100% coverage of critical paths",
                "Mock external dependencies",
                "Test agent interactions",
                "Validate error handling"
            ],
            technical_requirements=[
                "pytest framework",
                "Mock/patch for external services",
                "Async test support",
                "Coverage reporting"
            ],
            risks=["Complex mocking requirements", "Async testing challenges"],
            assigned_agent="QA"
        ))
        
        self.tasks.append(ProjectTask(
            id="TEST-002",
            title="Implement integration test suite",
            description="Create integration tests for multi-agent workflows",
            category=self.task_categories['testing'],
            priority="P0",
            effort_hours=10,
            dependencies=["TEST-001"],
            acceptance_criteria=[
                "Test agent coordination",
                "Validate knowledge base integration",
                "Test RAG system responses",
                "Verify Guardian functionality"
            ],
            technical_requirements=[
                "Integration test framework",
                "Test data management",
                "Service virtualization",
                "Performance benchmarking"
            ],
            risks=["Test environment complexity", "Data dependencies"],
            assigned_agent="QA"
        ))
        
        self.tasks.append(ProjectTask(
            id="TEST-003",
            title="Implement the 'killer demo' - scaling issue detection",
            description="Create demonstration showing detection of scaling issues before production",
            category=self.task_categories['testing'],
            priority="P0",
            effort_hours=8,
            dependencies=["TEST-001", "CLI-001"],
            acceptance_criteria=[
                "Detects n+1 query problems",
                "Identifies memory leaks",
                "Catches inefficient algorithms",
                "Provides fix recommendations"
            ],
            technical_requirements=[
                "Code analysis engine",
                "Pattern matching system",
                "Performance profiling",
                "Recommendation engine"
            ],
            risks=["False positive rate", "Performance overhead"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="TEST-004",
            title="Create regression test suite with prevention system",
            description="Build regression testing framework with automatic prevention",
            category=self.task_categories['testing'],
            priority="P1",
            effort_hours=6,
            dependencies=["TEST-002"],
            acceptance_criteria=[
                "Baseline quality metrics",
                "Automatic regression detection",
                "Historical tracking",
                "Prevention recommendations"
            ],
            technical_requirements=[
                "Regression framework",
                "Metric tracking system",
                "Historical database",
                "Alert mechanism"
            ],
            risks=["Baseline drift", "Metric reliability"],
            assigned_agent="QA"
        ))
    
    def _add_deployment_tasks(self):
        """Add cloud deployment tasks"""
        
        self.tasks.append(ProjectTask(
            id="DEPLOY-001",
            title="Create GCP deployment configuration",
            description="Set up GCP infrastructure for Gemini Enterprise Architect",
            category=self.task_categories['deployment'],
            priority="P0",
            effort_hours=8,
            dependencies=[],
            acceptance_criteria=[
                "Terraform/Pulumi configuration",
                "GKE cluster setup",
                "Vertex AI integration",
                "Cloud Build pipeline"
            ],
            technical_requirements=[
                "Infrastructure as Code",
                "Container orchestration",
                "Service mesh setup",
                "CI/CD pipeline"
            ],
            risks=["GCP quota limits", "Configuration complexity"],
            assigned_agent="Architect"
        ))
        
        self.tasks.append(ProjectTask(
            id="DEPLOY-002",
            title="Implement containerization for all agents",
            description="Create Docker containers for agent deployment",
            category=self.task_categories['deployment'],
            priority="P0",
            effort_hours=6,
            dependencies=["DEPLOY-001"],
            acceptance_criteria=[
                "Dockerfile for each agent",
                "Multi-stage builds",
                "Security scanning",
                "Size optimization"
            ],
            technical_requirements=[
                "Docker best practices",
                "Base image selection",
                "Layer optimization",
                "Security hardening"
            ],
            risks=["Image size", "Security vulnerabilities"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="DEPLOY-003",
            title="Set up Vertex AI knowledge base infrastructure",
            description="Deploy and configure Vertex AI for RAG system",
            category=self.task_categories['deployment'],
            priority="P0",
            effort_hours=10,
            dependencies=["DEPLOY-001"],
            acceptance_criteria=[
                "Vertex AI endpoints configured",
                "Embedding models deployed",
                "Vector database initialized",
                "RAG pipeline operational"
            ],
            technical_requirements=[
                "Vertex AI configuration",
                "Model deployment",
                "Index creation",
                "Endpoint management"
            ],
            risks=["Cost management", "Model performance"],
            assigned_agent="Architect"
        ))
        
        self.tasks.append(ProjectTask(
            id="DEPLOY-004",
            title="Implement auto-scaling and load balancing",
            description="Configure automatic scaling for agent workloads",
            category=self.task_categories['deployment'],
            priority="P1",
            effort_hours=6,
            dependencies=["DEPLOY-002"],
            acceptance_criteria=[
                "HPA/VPA configured",
                "Load balancer setup",
                "Health checks implemented",
                "Graceful shutdown handling"
            ],
            technical_requirements=[
                "Kubernetes autoscaling",
                "Metrics server setup",
                "Ingress configuration",
                "Circuit breaker pattern"
            ],
            risks=["Scaling delays", "Cost overruns"],
            assigned_agent="Architect"
        ))
    
    def _add_documentation_tasks(self):
        """Add documentation tasks"""
        
        self.tasks.append(ProjectTask(
            id="DOC-001",
            title="Create comprehensive user documentation",
            description="Write user guides and tutorials for Gemini Enterprise Architect",
            category=self.task_categories['documentation'],
            priority="P1",
            effort_hours=12,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "Getting started guide",
                "Agent capability documentation",
                "Workflow examples",
                "Troubleshooting guide"
            ],
            technical_requirements=[
                "Markdown documentation",
                "Code examples",
                "Video tutorials",
                "Interactive demos"
            ],
            risks=["Documentation drift", "Maintenance burden"],
            assigned_agent="PM"
        ))
        
        self.tasks.append(ProjectTask(
            id="DOC-002",
            title="Create API documentation for agent interfaces",
            description="Document all agent APIs and integration points",
            category=self.task_categories['documentation'],
            priority="P1",
            effort_hours=8,
            dependencies=[],
            acceptance_criteria=[
                "OpenAPI specifications",
                "Code documentation",
                "Integration examples",
                "SDK documentation"
            ],
            technical_requirements=[
                "OpenAPI/Swagger",
                "Docstring standards",
                "Auto-generation tools",
                "Version management"
            ],
            risks=["API changes", "Version compatibility"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="DOC-003",
            title="Develop architectural decision records (ADRs)",
            description="Document key architectural decisions and rationale",
            category=self.task_categories['documentation'],
            priority="P2",
            effort_hours=6,
            dependencies=[],
            acceptance_criteria=[
                "ADR template created",
                "Key decisions documented",
                "Trade-offs explained",
                "Future considerations noted"
            ],
            technical_requirements=[
                "ADR format",
                "Decision tracking",
                "Review process",
                "Version control"
            ],
            risks=["Decision complexity", "Stakeholder alignment"],
            assigned_agent="Architect"
        ))
    
    def _add_monitoring_tasks(self):
        """Add monitoring and observability tasks"""
        
        self.tasks.append(ProjectTask(
            id="MON-001",
            title="Implement DORA metrics tracking",
            description="Set up comprehensive DORA metrics monitoring",
            category=self.task_categories['monitoring'],
            priority="P0",
            effort_hours=8,
            dependencies=["DEPLOY-001"],
            acceptance_criteria=[
                "Deployment frequency tracking",
                "Lead time measurement",
                "MTTR calculation",
                "Change failure rate monitoring"
            ],
            technical_requirements=[
                "Metrics collection system",
                "Time series database",
                "Dashboard creation",
                "Alert configuration"
            ],
            risks=["Metric accuracy", "Data volume"],
            assigned_agent="PM"
        ))
        
        self.tasks.append(ProjectTask(
            id="MON-002",
            title="Set up distributed tracing for agent interactions",
            description="Implement tracing to monitor multi-agent workflows",
            category=self.task_categories['monitoring'],
            priority="P1",
            effort_hours=6,
            dependencies=["MON-001"],
            acceptance_criteria=[
                "Trace context propagation",
                "Span collection",
                "Latency analysis",
                "Dependency mapping"
            ],
            technical_requirements=[
                "OpenTelemetry integration",
                "Trace collector setup",
                "Sampling strategy",
                "Storage backend"
            ],
            risks=["Performance overhead", "Storage costs"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="MON-003",
            title="Create operational dashboards",
            description="Build dashboards for system health and performance",
            category=self.task_categories['monitoring'],
            priority="P1",
            effort_hours=6,
            dependencies=["MON-001"],
            acceptance_criteria=[
                "System health dashboard",
                "Agent performance metrics",
                "User activity tracking",
                "Cost monitoring"
            ],
            technical_requirements=[
                "Grafana/similar tool",
                "Query optimization",
                "Auto-refresh setup",
                "Mobile responsiveness"
            ],
            risks=["Dashboard complexity", "Query performance"],
            assigned_agent="PM"
        ))
    
    def _add_security_tasks(self):
        """Add security and compliance tasks"""
        
        self.tasks.append(ProjectTask(
            id="SEC-001",
            title="Implement authentication and authorization",
            description="Add security controls for agent access",
            category=self.task_categories['security'],
            priority="P0",
            effort_hours=10,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "OAuth2/OIDC integration",
                "Role-based access control",
                "API key management",
                "Audit logging"
            ],
            technical_requirements=[
                "Identity provider integration",
                "JWT handling",
                "Permission system",
                "Audit trail"
            ],
            risks=["Authentication complexity", "Performance impact"],
            assigned_agent="Architect"
        ))
        
        self.tasks.append(ProjectTask(
            id="SEC-002",
            title="Perform security vulnerability assessment",
            description="Conduct comprehensive security testing",
            category=self.task_categories['security'],
            priority="P0",
            effort_hours=8,
            dependencies=["TEST-001"],
            acceptance_criteria=[
                "SAST/DAST scanning",
                "Dependency vulnerability check",
                "Penetration testing",
                "Security report generation"
            ],
            technical_requirements=[
                "Security scanning tools",
                "Vulnerability database",
                "Remediation tracking",
                "Compliance validation"
            ],
            risks=["Critical vulnerabilities", "Remediation time"],
            assigned_agent="QA"
        ))
        
        self.tasks.append(ProjectTask(
            id="SEC-003",
            title="Implement data encryption and privacy controls",
            description="Add encryption for data at rest and in transit",
            category=self.task_categories['security'],
            priority="P0",
            effort_hours=6,
            dependencies=["SEC-001"],
            acceptance_criteria=[
                "TLS for all communications",
                "Encryption at rest",
                "Key management system",
                "PII handling compliance"
            ],
            technical_requirements=[
                "TLS configuration",
                "KMS integration",
                "Encryption libraries",
                "Data classification"
            ],
            risks=["Performance overhead", "Key management complexity"],
            assigned_agent="Developer"
        ))
    
    def _add_performance_tasks(self):
        """Add performance optimization tasks"""
        
        self.tasks.append(ProjectTask(
            id="PERF-001",
            title="Optimize agent response times",
            description="Improve performance of agent operations",
            category=self.task_categories['performance'],
            priority="P1",
            effort_hours=8,
            dependencies=["TEST-002"],
            acceptance_criteria=[
                "Sub-second response for simple queries",
                "Efficient caching strategy",
                "Query optimization",
                "Resource pooling"
            ],
            technical_requirements=[
                "Performance profiling",
                "Cache implementation",
                "Connection pooling",
                "Async optimization"
            ],
            risks=["Cache invalidation", "Memory usage"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="PERF-002",
            title="Implement knowledge base indexing optimization",
            description="Optimize RAG system for faster retrieval",
            category=self.task_categories['performance'],
            priority="P1",
            effort_hours=6,
            dependencies=["DEPLOY-003"],
            acceptance_criteria=[
                "Optimized embedding generation",
                "Efficient vector search",
                "Index optimization",
                "Query caching"
            ],
            technical_requirements=[
                "Vector index tuning",
                "Batch processing",
                "Parallel search",
                "Result caching"
            ],
            risks=["Index size growth", "Accuracy trade-offs"],
            assigned_agent="Architect"
        ))
    
    def _add_integration_tasks(self):
        """Add system integration tasks"""
        
        self.tasks.append(ProjectTask(
            id="INT-001",
            title="Create IDE plugins for popular editors",
            description="Develop plugins for VS Code, IntelliJ, etc.",
            category=self.task_categories['integration'],
            priority="P2",
            effort_hours=16,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "VS Code extension",
                "IntelliJ plugin",
                "Real-time validation",
                "Code completion support"
            ],
            technical_requirements=[
                "Extension APIs",
                "Language server protocol",
                "WebSocket communication",
                "UI components"
            ],
            risks=["API changes", "Maintenance overhead"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="INT-002",
            title="Integrate with existing CI/CD pipelines",
            description="Add support for Jenkins, GitHub Actions, GitLab CI",
            category=self.task_categories['integration'],
            priority="P1",
            effort_hours=8,
            dependencies=["CLI-001"],
            acceptance_criteria=[
                "GitHub Actions workflow",
                "Jenkins plugin",
                "GitLab CI template",
                "Build status reporting"
            ],
            technical_requirements=[
                "CI/CD APIs",
                "Webhook handling",
                "Status reporting",
                "Artifact management"
            ],
            risks=["Platform differences", "API limitations"],
            assigned_agent="Developer"
        ))
        
        self.tasks.append(ProjectTask(
            id="INT-003",
            title="Create Slack/Teams integration for notifications",
            description="Build chat integrations for team collaboration",
            category=self.task_categories['integration'],
            priority="P2",
            effort_hours=6,
            dependencies=["MON-001"],
            acceptance_criteria=[
                "Slack bot implementation",
                "Teams app creation",
                "Alert notifications",
                "Interactive commands"
            ],
            technical_requirements=[
                "Bot frameworks",
                "Webhook configuration",
                "OAuth setup",
                "Message formatting"
            ],
            risks=["Rate limiting", "Authentication complexity"],
            assigned_agent="Developer"
        ))
    
    def _calculate_value_scores(self):
        """Calculate value scores for all tasks"""
        for task in self.tasks:
            # Base value on priority
            priority_values = {"P0": 100, "P1": 75, "P2": 50, "P3": 25}
            base_value = priority_values.get(task.priority, 50)
            
            # Adjust for effort (value per hour)
            effort_factor = base_value / max(task.effort_hours, 1)
            
            # Dependency bonus (enabling other tasks)
            dependency_bonus = len([t for t in self.tasks if task.id in t.dependencies]) * 10
            
            # Risk penalty
            risk_penalty = len(task.risks) * 5
            
            task.value_score = max(0, base_value + dependency_bonus - risk_penalty + effort_factor)
    
    def _assess_dora_impacts(self):
        """Assess DORA metric impacts for each task"""
        for task in self.tasks:
            task.dora_impact = {}
            
            # Deployment Frequency impact
            if task.category in ['CLI Integration', 'Cloud Deployment', 'System Integration']:
                task.dora_impact['deployment_frequency'] = 'High'
            elif task.category in ['Testing & Validation', 'Monitoring & Observability']:
                task.dora_impact['deployment_frequency'] = 'Medium'
            else:
                task.dora_impact['deployment_frequency'] = 'Low'
            
            # Lead Time impact
            if task.category in ['CLI Integration', 'Performance Optimization']:
                task.dora_impact['lead_time'] = 'High'
            elif task.category in ['Testing & Validation', 'Documentation']:
                task.dora_impact['lead_time'] = 'Medium'
            else:
                task.dora_impact['lead_time'] = 'Low'
            
            # MTTR impact
            if task.category in ['Monitoring & Observability', 'Testing & Validation']:
                task.dora_impact['mttr'] = 'High'
            elif task.category in ['Documentation', 'Security & Compliance']:
                task.dora_impact['mttr'] = 'Medium'
            else:
                task.dora_impact['mttr'] = 'Low'
            
            # Change Failure Rate impact
            if task.category in ['Testing & Validation', 'Security & Compliance']:
                task.dora_impact['change_failure_rate'] = 'High'
            elif task.category in ['CLI Integration', 'Cloud Deployment']:
                task.dora_impact['change_failure_rate'] = 'Medium'
            else:
                task.dora_impact['change_failure_rate'] = 'Low'
    
    def _optimize_task_ordering(self):
        """Optimize task order based on dependencies and value"""
        # Sort by priority first, then by value score
        self.tasks.sort(key=lambda x: (x.priority, -x.value_score))
    
    def export_to_json(self, filename: str = "gemini_tasks.json"):
        """Export tasks to JSON format"""
        tasks_dict = []
        for task in self.tasks:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'category': task.category,
                'priority': task.priority,
                'effort_hours': task.effort_hours,
                'dependencies': task.dependencies,
                'acceptance_criteria': task.acceptance_criteria,
                'technical_requirements': task.technical_requirements,
                'risks': task.risks,
                'value_score': task.value_score,
                'dora_impact': task.dora_impact,
                'assigned_agent': task.assigned_agent,
                'status': task.status
            }
            tasks_dict.append(task_dict)
        
        with open(filename, 'w') as f:
            json.dump(tasks_dict, f, indent=2)
        
        return filename
    
    def generate_sprint_plan(self, sprint_capacity_hours: int = 80) -> List[List[ProjectTask]]:
        """Generate sprint plan based on capacity"""
        sprints = []
        current_sprint = []
        current_capacity = 0
        
        # Process tasks in order
        pending_tasks = [t for t in self.tasks if t.status == 'pending']
        
        for task in pending_tasks:
            # Check dependencies
            deps_complete = all(
                any(t.id == dep and t.status == 'completed' for t in self.tasks)
                or dep in [t.id for t in current_sprint]
                for dep in task.dependencies
            )
            
            if deps_complete:
                if current_capacity + task.effort_hours <= sprint_capacity_hours:
                    current_sprint.append(task)
                    current_capacity += task.effort_hours
                else:
                    if current_sprint:
                        sprints.append(current_sprint)
                    current_sprint = [task]
                    current_capacity = task.effort_hours
        
        if current_sprint:
            sprints.append(current_sprint)
        
        return sprints
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of all tasks"""
        total_effort = sum(t.effort_hours for t in self.tasks)
        
        category_breakdown = {}
        for task in self.tasks:
            if task.category not in category_breakdown:
                category_breakdown[task.category] = {
                    'count': 0,
                    'effort_hours': 0,
                    'avg_value_score': 0
                }
            category_breakdown[task.category]['count'] += 1
            category_breakdown[task.category]['effort_hours'] += task.effort_hours
            category_breakdown[task.category]['avg_value_score'] += task.value_score
        
        # Calculate averages
        for category in category_breakdown:
            count = category_breakdown[category]['count']
            category_breakdown[category]['avg_value_score'] /= count
        
        priority_breakdown = {
            'P0': len([t for t in self.tasks if t.priority == 'P0']),
            'P1': len([t for t in self.tasks if t.priority == 'P1']),
            'P2': len([t for t in self.tasks if t.priority == 'P2']),
            'P3': len([t for t in self.tasks if t.priority == 'P3'])
        }
        
        return {
            'total_tasks': len(self.tasks),
            'total_effort_hours': total_effort,
            'estimated_duration_weeks': total_effort / 40,  # Assuming 40 hours/week
            'category_breakdown': category_breakdown,
            'priority_breakdown': priority_breakdown,
            'high_value_tasks': [t.id for t in sorted(self.tasks, key=lambda x: -x.value_score)[:10]],
            'critical_path': [t.id for t in self.tasks if t.priority == 'P0' and not t.dependencies]
        }

# Generate tasks and export
if __name__ == "__main__":
    generator = GeminiPMTaskGenerator()
    tasks = generator.generate_comprehensive_tasks()
    
    # Export to JSON
    filename = generator.export_to_json("/Users/stuartgano/Documents/gemini-cli/tasks/gemini_tasks.json")
    print(f"Generated {len(tasks)} tasks and exported to {filename}")
    
    # Generate sprint plan
    sprints = generator.generate_sprint_plan()
    print(f"\nSprint Plan ({len(sprints)} sprints):")
    for i, sprint in enumerate(sprints, 1):
        sprint_hours = sum(t.effort_hours for t in sprint)
        print(f"  Sprint {i}: {len(sprint)} tasks, {sprint_hours} hours")
        for task in sprint:
            print(f"    - [{task.priority}] {task.id}: {task.title} ({task.effort_hours}h)")
    
    # Generate summary report
    report = generator.get_summary_report()
    print(f"\nSummary Report:")
    print(f"  Total Tasks: {report['total_tasks']}")
    print(f"  Total Effort: {report['total_effort_hours']} hours")
    print(f"  Estimated Duration: {report['estimated_duration_weeks']:.1f} weeks")
    print(f"  Priority Breakdown: {report['priority_breakdown']}")
    print(f"  Critical Path Tasks: {report['critical_path']}")
    print(f"  Top 5 High-Value Tasks: {report['high_value_tasks'][:5]}")