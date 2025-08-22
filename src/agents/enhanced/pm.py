"""
Enhanced PM Agent
BMAD Project Manager enhanced with DORA metrics and standards enforcement
"""

import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

from ..unified_agent_base import UnifiedAgent, AgentConfig


class DORATracker:
    """Track and optimize DORA metrics"""
    
    def __init__(self):
        self.metrics_history = {
            'deployment_frequency': [],
            'lead_time': [],
            'mttr': [],
            'change_failure_rate': []
        }
        
    def analyze_requirements_for_dora(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how requirements will impact DORA metrics"""
        analysis = {
            'deployment_frequency_impact': 'neutral',
            'lead_time_impact': 'neutral',
            'mttr_impact': 'neutral',
            'failure_rate_impact': 'neutral',
            'recommendations': []
        }
        
        for req in requirements:
            # Check for patterns that affect DORA metrics
            if 'microservices' in req.get('description', '').lower():
                analysis['deployment_frequency_impact'] = 'positive'
                analysis['recommendations'].append('Microservices enable independent deployments')
                
            if 'monitoring' in req.get('description', '').lower():
                analysis['mttr_impact'] = 'positive'
                analysis['recommendations'].append('Monitoring reduces time to detect issues')
                
            if 'testing' in req.get('description', '').lower():
                analysis['failure_rate_impact'] = 'positive'
                analysis['recommendations'].append('Comprehensive testing reduces failure rate')
                
            if 'ci/cd' in req.get('description', '').lower():
                analysis['lead_time_impact'] = 'positive'
                analysis['recommendations'].append('CI/CD automation reduces lead time')
                
        return analysis
    
    def suggest_improvements(self, current_metrics: Dict[str, float]) -> List[Dict[str, str]]:
        """Suggest improvements based on current metrics"""
        suggestions = []
        
        if current_metrics.get('deployment_frequency', 0) < 1:  # Less than daily
            suggestions.append({
                'metric': 'Deployment Frequency',
                'current': f"{current_metrics.get('deployment_frequency', 0)}/day",
                'target': '1+/day',
                'action': 'Implement feature flags for safer frequent deployments'
            })
            
        if current_metrics.get('lead_time', 24) > 24:  # More than 24 hours
            suggestions.append({
                'metric': 'Lead Time',
                'current': f"{current_metrics.get('lead_time', 24)} hours",
                'target': '<24 hours',
                'action': 'Automate testing and deployment pipeline'
            })
            
        return suggestions


class RequirementsAnalyzer:
    """Analyze and enhance requirements with standards"""
    
    def __init__(self, standards_enforcer):
        self.standards_enforcer = standards_enforcer
        
    def analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """Analyze a requirement for completeness and standards"""
        analysis = {
            'is_complete': True,
            'has_acceptance_criteria': False,
            'is_measurable': False,
            'has_performance_criteria': False,
            'security_considered': False,
            'suggestions': []
        }
        
        # Check for acceptance criteria
        if 'given' in requirement.lower() and 'when' in requirement.lower() and 'then' in requirement.lower():
            analysis['has_acceptance_criteria'] = True
        else:
            analysis['suggestions'].append('Add Given/When/Then acceptance criteria')
            analysis['is_complete'] = False
            
        # Check for measurable criteria
        if any(char.isdigit() for char in requirement):
            analysis['is_measurable'] = True
        else:
            analysis['suggestions'].append('Add measurable success criteria')
            
        # Check for performance criteria
        if any(word in requirement.lower() for word in ['latency', 'throughput', 'response time', 'performance']):
            analysis['has_performance_criteria'] = True
        else:
            analysis['suggestions'].append('Consider performance requirements')
            
        # Check for security
        if any(word in requirement.lower() for word in ['security', 'authentication', 'authorization', 'encryption']):
            analysis['security_considered'] = True
        else:
            analysis['suggestions'].append('Consider security implications')
            
        return analysis
    
    def enhance_requirement(self, requirement: str, analysis: Dict[str, Any]) -> str:
        """Enhance requirement based on analysis"""
        enhanced = requirement
        
        if not analysis['has_acceptance_criteria']:
            enhanced += "\n\nAcceptance Criteria:\n- Given: [initial state]\n- When: [action]\n- Then: [expected outcome]"
            
        if not analysis['has_performance_criteria']:
            enhanced += "\n\nPerformance Criteria:\n- Response time: <100ms p99\n- Throughput: 1000 RPS"
            
        if not analysis['security_considered']:
            enhanced += "\n\nSecurity Requirements:\n- Authentication required\n- Data encryption in transit and at rest"
            
        return enhanced


class EnhancedPM(UnifiedAgent):
    """
    BMAD Project Manager enhanced with DORA metrics and standards enforcement
    Pat - Project Manager focused on requirements, planning, and delivery optimization
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.dora_tracker = DORATracker()
        self.requirements_analyzer = RequirementsAnalyzer(self.standards_enforcer)
        
        # PRD components
        self.epics = []
        self.stories = []
        self.nfrs = []
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD PM configuration"""
        return AgentConfig(
            id="pm",
            name="Pat",
            title="Project Manager",
            icon="📋",
            when_to_use="Use for creating PRDs, managing epics and stories, tracking project progress",
            persona={
                'role': 'Strategic Project Manager & Delivery Optimizer',
                'style': 'Organized, strategic, results-driven, collaborative',
                'identity': 'Project manager ensuring successful delivery through clear requirements and planning',
                'focus': 'Requirements clarity, delivery optimization, stakeholder alignment',
                'core_principles': [
                    'Clear and measurable requirements',
                    'Data-driven decision making',
                    'Continuous delivery optimization',
                    'Stakeholder communication',
                    'Risk mitigation'
                ]
            },
            commands=[
                {'name': 'create-prd', 'description': 'Create Product Requirements Document'},
                {'name': 'create-epic', 'description': 'Create new epic'},
                {'name': 'create-story', 'description': 'Create user story'},
                {'name': 'track-metrics', 'description': 'Track DORA metrics'},
                {'name': 'prioritize-backlog', 'description': 'Prioritize product backlog'}
            ],
            dependencies={
                'templates': ['prd-tmpl.yaml', 'story-tmpl.yaml'],
                'tasks': ['create-doc.md', 'create-next-story.md'],
                'checklists': ['pm-checklist.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PM-specific tasks"""
        
        if task == "create_prd":
            return self.create_prd(context)
        elif task == "create_epic":
            return self.create_epic(context)
        elif task == "create_story":
            return self.create_story(context)
        elif task == "track_metrics":
            return self.track_dora_metrics(context)
        elif task == "prioritize_backlog":
            return self.prioritize_backlog(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def create_prd(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive PRD with DORA optimization"""
        
        # Load BMAD PRD template
        template = self.load_bmad_template('prd-tmpl.yaml')
        
        # Extract from project brief if available
        project_brief = context.get('project_brief', {})
        
        # Build PRD structure
        prd = {
            'title': project_brief.get('title', 'Product Requirements Document'),
            'version': '1.0',
            'created_date': datetime.now().isoformat(),
            'author': 'PM Agent (Pat)',
            
            # Executive Summary
            'executive_summary': {
                'vision': project_brief.get('vision', ''),
                'objectives': project_brief.get('objectives', []),
                'success_metrics': self._define_success_metrics(context),
                'timeline': self._create_timeline(context)
            },
            
            # Functional Requirements
            'functional_requirements': self._create_functional_requirements(context),
            
            # Non-Functional Requirements with standards
            'non_functional_requirements': self._create_nfrs_with_standards(context),
            
            # Epics and Stories
            'epics': self._create_epics(context),
            'stories': self._create_initial_stories(context),
            
            # DORA Optimization
            'dora_optimization': {
                'current_metrics': self.dora_tracker.metrics_history,
                'impact_analysis': self.dora_tracker.analyze_requirements_for_dora(
                    self._create_functional_requirements(context)
                ),
                'improvement_plan': self.dora_tracker.suggest_improvements({
                    'deployment_frequency': 0.5,
                    'lead_time': 48
                })
            },
            
            # Technical Constraints from Gemini
            'technical_constraints': {
                'scaling_requirements': self._define_scaling_requirements(context),
                'security_requirements': self._define_security_requirements(context),
                'compliance_requirements': context.get('compliance', [])
            },
            
            # Risk Analysis
            'risk_analysis': self._analyze_risks(context),
            
            # Dependencies
            'dependencies': self._identify_dependencies(context),
            
            # Acceptance Criteria
            'acceptance_criteria': self._define_acceptance_criteria(context)
        }
        
        # Enforce standards on all requirements
        prd = self._enforce_standards_on_prd(prd)
        
        # Teach about PRD best practices
        self.teaching_engine.teach(
            "PRD Best Practices",
            {
                'what': "Created PRD with DORA optimization",
                'why': "DORA metrics predict delivery performance",
                'how': "Each requirement assessed for metric impact",
                'example': prd['dora_optimization']['impact_analysis']
            }
        )
        
        return prd
    
    def create_epic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create epic with service recommendations"""
        
        epic = {
            'id': f"EPIC-{len(self.epics) + 1:03d}",
            'title': context.get('title', 'New Epic'),
            'description': context.get('description', ''),
            'business_value': context.get('business_value', 'Medium'),
            'priority': context.get('priority', 'P2'),
            
            # Service recommendations from Gemini
            'service_recommendations': self.service_advisor.recommend(context),
            
            # Acceptance criteria
            'acceptance_criteria': self._create_acceptance_criteria(context),
            
            # Success metrics
            'success_metrics': self._define_epic_metrics(context),
            
            # Stories
            'stories': [],
            
            # Dependencies
            'dependencies': context.get('dependencies', []),
            
            # Risks
            'risks': self._assess_epic_risks(context),
            
            # Timeline
            'estimated_duration': self._estimate_duration(context),
            
            'created_date': datetime.now().isoformat(),
            'status': 'Draft'
        }
        
        # Analyze for standards compliance
        violations = self.standards_enforcer.check({
            'type': 'epic',
            'content': epic
        })
        
        if violations:
            epic['standards_violations'] = violations
            self.teach_and_correct(violations, context)
        
        self.epics.append(epic)
        return epic
    
    def create_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create user story with technical requirements"""
        
        # Load BMAD story template
        template = self.load_bmad_template('story-tmpl.yaml')
        
        story = {
            'id': f"STORY-{len(self.stories) + 1:03d}",
            'epic_id': context.get('epic_id'),
            'title': context.get('title', 'New Story'),
            
            # User story format
            'user_story': self._format_user_story(context),
            
            # Acceptance criteria with Given/When/Then
            'acceptance_criteria': self._create_story_acceptance_criteria(context),
            
            # Technical requirements
            'technical_requirements': {
                'api_endpoints': context.get('api_endpoints', []),
                'data_models': context.get('data_models', []),
                'performance_criteria': self._define_performance_criteria(context),
                'security_requirements': self._define_story_security(context)
            },
            
            # Definition of Done
            'definition_of_done': self._create_dod(context),
            
            # Estimates
            'estimates': {
                'story_points': self._estimate_story_points(context),
                'development_hours': self._estimate_dev_hours(context),
                'testing_hours': self._estimate_test_hours(context)
            },
            
            # Dependencies
            'dependencies': context.get('dependencies', []),
            
            # Test scenarios
            'test_scenarios': self._create_test_scenarios(context),
            
            'created_date': datetime.now().isoformat(),
            'status': 'Draft',
            'priority': context.get('priority', 'P2')
        }
        
        # Analyze requirement quality
        analysis = self.requirements_analyzer.analyze_requirement(story['user_story'])
        if not analysis['is_complete']:
            story['user_story'] = self.requirements_analyzer.enhance_requirement(
                story['user_story'], 
                analysis
            )
            story['quality_enhancements'] = analysis['suggestions']
        
        self.stories.append(story)
        return story
    
    def track_dora_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Track and analyze DORA metrics"""
        
        current_metrics = context.get('metrics', {})
        
        # Update metrics history
        if 'deployment_frequency' in current_metrics:
            self.dora_tracker.metrics_history['deployment_frequency'].append({
                'value': current_metrics['deployment_frequency'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Get improvement suggestions
        suggestions = self.dora_tracker.suggest_improvements(current_metrics)
        
        # Teach about DORA
        self.teaching_engine.teach(
            "DORA Metrics",
            {
                'what': "Tracking DevOps performance metrics",
                'why': "DORA metrics predict software delivery performance",
                'how': "Optimize for: deployment frequency, lead time, MTTR, failure rate",
                'example': suggestions[0] if suggestions else None
            }
        )
        
        return {
            'current_metrics': current_metrics,
            'historical_metrics': self.dora_tracker.metrics_history,
            'improvement_suggestions': suggestions,
            'trend_analysis': self._analyze_trends()
        }
    
    def prioritize_backlog(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize backlog based on value and DORA impact"""
        
        items = context.get('backlog_items', self.stories)
        
        # Score each item
        scored_items = []
        for item in items:
            score = self._calculate_priority_score(item)
            scored_items.append({
                **item,
                'priority_score': score,
                'priority_factors': {
                    'business_value': self._score_business_value(item),
                    'dora_impact': self._score_dora_impact(item),
                    'risk_reduction': self._score_risk_reduction(item),
                    'dependency_count': len(item.get('dependencies', []))
                }
            })
        
        # Sort by priority score
        prioritized = sorted(scored_items, key=lambda x: x['priority_score'], reverse=True)
        
        # Teach about prioritization
        self.teaching_engine.teach(
            "Backlog Prioritization",
            {
                'what': "Prioritized backlog using value and DORA impact",
                'why': "Focus on items that deliver value and improve metrics",
                'how': "Score = Business Value × DORA Impact × Risk Reduction",
                'example': f"Top priority: {prioritized[0]['title']}" if prioritized else None
            }
        )
        
        return prioritized
    
    def _create_functional_requirements(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create functional requirements"""
        requirements = []
        
        # Extract from context or generate
        for i, req_text in enumerate(context.get('requirements', []), 1):
            req = {
                'id': f"FR-{i:03d}",
                'description': req_text,
                'priority': 'P1' if i <= 3 else 'P2',
                'category': self._categorize_requirement(req_text)
            }
            
            # Analyze and enhance
            analysis = self.requirements_analyzer.analyze_requirement(req_text)
            if not analysis['is_complete']:
                req['description'] = self.requirements_analyzer.enhance_requirement(req_text, analysis)
                req['enhancements'] = analysis['suggestions']
            
            requirements.append(req)
        
        return requirements
    
    def _create_nfrs_with_standards(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create NFRs enforcing enterprise standards"""
        
        nfrs = [
            {
                'id': 'NFR-001',
                'category': 'Performance',
                'requirement': 'System must handle 10,000 concurrent users',
                'metric': 'Response time <100ms p99',
                'validation': 'Load testing with 10K virtual users'
            },
            {
                'id': 'NFR-002',
                'category': 'Scalability',
                'requirement': 'System must auto-scale based on load',
                'metric': 'Scale from 1 to 100 pods in <2 minutes',
                'validation': 'Chaos engineering tests'
            },
            {
                'id': 'NFR-003',
                'category': 'Security',
                'requirement': 'All data must be encrypted',
                'metric': 'AES-256 encryption at rest, TLS 1.3 in transit',
                'validation': 'Security audit and penetration testing'
            },
            {
                'id': 'NFR-004',
                'category': 'Availability',
                'requirement': '99.99% uptime SLA',
                'metric': '<52 minutes downtime per year',
                'validation': 'Multi-region deployment with failover'
            },
            {
                'id': 'NFR-005',
                'category': 'Observability',
                'requirement': 'Full system observability',
                'metric': '100% trace coverage, <1s log ingestion',
                'validation': 'Distributed tracing and centralized logging'
            }
        ]
        
        # Add context-specific NFRs
        if context.get('compliance'):
            nfrs.append({
                'id': f'NFR-{len(nfrs)+1:03d}',
                'category': 'Compliance',
                'requirement': f"Meet {context['compliance']} requirements",
                'metric': '100% compliance score',
                'validation': 'Compliance audit'
            })
        
        return nfrs
    
    def _create_epics(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create initial epics"""
        
        epic_ideas = [
            {'title': 'User Authentication & Authorization', 'priority': 'P1'},
            {'title': 'Core Business Logic', 'priority': 'P1'},
            {'title': 'Data Management & Storage', 'priority': 'P1'},
            {'title': 'API Development', 'priority': 'P2'},
            {'title': 'UI/UX Implementation', 'priority': 'P2'},
            {'title': 'Monitoring & Observability', 'priority': 'P3'}
        ]
        
        for epic_idea in epic_ideas:
            epic_context = {**context, **epic_idea}
            self.create_epic(epic_context)
        
        return self.epics
    
    def _create_initial_stories(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create initial stories for epics"""
        
        for epic in self.epics[:3]:  # Create stories for first 3 epics
            for i in range(3):  # 3 stories per epic
                story_context = {
                    'epic_id': epic['id'],
                    'title': f"{epic['title']} - Story {i+1}",
                    'priority': epic['priority']
                }
                self.create_story(story_context)
        
        return self.stories
    
    def _enforce_standards_on_prd(self, prd: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce enterprise standards on entire PRD"""
        
        # Check all functional requirements
        for req in prd['functional_requirements']:
            violations = self.standards_enforcer.check({'type': 'requirement', **req})
            if violations:
                req['standards_notes'] = violations
        
        # Ensure NFRs meet minimum standards
        required_nfr_categories = ['Performance', 'Security', 'Scalability', 'Availability']
        existing_categories = [nfr['category'] for nfr in prd['non_functional_requirements']]
        
        for category in required_nfr_categories:
            if category not in existing_categories:
                prd['non_functional_requirements'].append({
                    'id': f'NFR-{len(prd["non_functional_requirements"])+1:03d}',
                    'category': category,
                    'requirement': f'Default {category} requirement',
                    'metric': 'To be defined',
                    'validation': 'To be defined',
                    'auto_generated': True
                })
        
        return prd
    
    # Helper methods
    def _define_success_metrics(self, context: Dict[str, Any]) -> List[str]:
        return [
            '10,000 active users within 6 months',
            '< 100ms response time p99',
            '99.99% uptime',
            'NPS score > 50'
        ]
    
    def _create_timeline(self, context: Dict[str, Any]) -> Dict[str, str]:
        start = datetime.now()
        return {
            'project_start': start.isoformat(),
            'mvp_launch': (start + timedelta(days=90)).isoformat(),
            'v1_release': (start + timedelta(days=180)).isoformat(),
            'v2_release': (start + timedelta(days=365)).isoformat()
        }
    
    def _define_scaling_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'initial_load': '1000 users',
            'target_load': '100,000 users',
            'peak_load': '1M users',
            'scaling_strategy': 'Horizontal auto-scaling with Cloud Run/GKE'
        }
    
    def _define_security_requirements(self, context: Dict[str, Any]) -> List[str]:
        return [
            'OAuth 2.0 authentication',
            'Role-based access control (RBAC)',
            'Data encryption at rest and in transit',
            'Regular security audits',
            'OWASP Top 10 compliance'
        ]
    
    def _analyze_risks(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        return [
            {
                'risk': 'Scaling bottlenecks',
                'probability': 'Medium',
                'impact': 'High',
                'mitigation': 'Design for horizontal scaling from day 1'
            },
            {
                'risk': 'Security vulnerabilities',
                'probability': 'Low',
                'impact': 'Critical',
                'mitigation': 'Regular security audits and penetration testing'
            }
        ]
    
    def _identify_dependencies(self, context: Dict[str, Any]) -> List[str]:
        return [
            'GCP project setup',
            'CI/CD pipeline configuration',
            'Domain and SSL certificates',
            'Third-party API integrations'
        ]
    
    def _define_acceptance_criteria(self, context: Dict[str, Any]) -> List[str]:
        return [
            'All functional requirements implemented and tested',
            'All NFRs met and validated',
            'Documentation complete',
            'Security audit passed',
            'Performance benchmarks achieved'
        ]
    
    def _categorize_requirement(self, req_text: str) -> str:
        if 'api' in req_text.lower():
            return 'API'
        elif 'ui' in req_text.lower() or 'interface' in req_text.lower():
            return 'UI'
        elif 'data' in req_text.lower():
            return 'Data'
        else:
            return 'Business Logic'
    
    def _create_acceptance_criteria(self, context: Dict[str, Any]) -> List[str]:
        return [
            'Given: System is deployed',
            'When: 10,000 users access simultaneously', 
            'Then: Response time remains <100ms'
        ]
    
    def _define_epic_metrics(self, context: Dict[str, Any]) -> List[str]:
        return ['Completion rate', 'Defect rate', 'User satisfaction']
    
    def _assess_epic_risks(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        return [{'risk': 'Scope creep', 'mitigation': 'Clear acceptance criteria'}]
    
    def _estimate_duration(self, context: Dict[str, Any]) -> str:
        return '4-6 weeks'
    
    def _format_user_story(self, context: Dict[str, Any]) -> str:
        return f"As a {context.get('user_type', 'user')}, I want to {context.get('action', 'perform action')}, so that {context.get('benefit', 'I get value')}"
    
    def _create_story_acceptance_criteria(self, context: Dict[str, Any]) -> List[str]:
        return [
            'Given: Initial state',
            'When: User action',
            'Then: Expected outcome'
        ]
    
    def _define_performance_criteria(self, context: Dict[str, Any]) -> Dict[str, str]:
        return {
            'response_time': '<100ms',
            'throughput': '1000 RPS',
            'error_rate': '<0.1%'
        }
    
    def _define_story_security(self, context: Dict[str, Any]) -> List[str]:
        return ['Authentication required', 'Input validation', 'Rate limiting']
    
    def _create_dod(self, context: Dict[str, Any]) -> List[str]:
        return [
            'Code complete and reviewed',
            'Unit tests written and passing',
            'Integration tests passing',
            'Documentation updated',
            'Deployed to staging'
        ]
    
    def _estimate_story_points(self, context: Dict[str, Any]) -> int:
        return 5
    
    def _estimate_dev_hours(self, context: Dict[str, Any]) -> int:
        return 16
    
    def _estimate_test_hours(self, context: Dict[str, Any]) -> int:
        return 8
    
    def _create_test_scenarios(self, context: Dict[str, Any]) -> List[str]:
        return [
            'Happy path scenario',
            'Error handling scenario',
            'Edge case scenario'
        ]
    
    def _analyze_trends(self) -> Dict[str, str]:
        return {
            'deployment_frequency': 'improving',
            'lead_time': 'stable',
            'mttr': 'improving',
            'failure_rate': 'decreasing'
        }
    
    def _calculate_priority_score(self, item: Dict[str, Any]) -> float:
        business_value = self._score_business_value(item)
        dora_impact = self._score_dora_impact(item)
        risk_reduction = self._score_risk_reduction(item)
        
        return business_value * dora_impact * risk_reduction
    
    def _score_business_value(self, item: Dict[str, Any]) -> float:
        priority = item.get('priority', 'P3')
        scores = {'P1': 3.0, 'P2': 2.0, 'P3': 1.0}
        return scores.get(priority, 1.0)
    
    def _score_dora_impact(self, item: Dict[str, Any]) -> float:
        # Score based on expected DORA improvement
        if 'ci/cd' in str(item).lower():
            return 3.0
        elif 'testing' in str(item).lower():
            return 2.0
        else:
            return 1.0
    
    def _score_risk_reduction(self, item: Dict[str, Any]) -> float:
        # Score based on risk mitigation
        if 'security' in str(item).lower():
            return 3.0
        elif 'scaling' in str(item).lower():
            return 2.0
        else:
            return 1.0