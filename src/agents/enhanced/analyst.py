"""
Enhanced Analyst Agent
BMAD Analyst enhanced with Gemini Enterprise Architect capabilities
Combines market research, brainstorming, and competitive analysis with Scout functionality
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import asyncio

from ..unified_agent_base import UnifiedAgent, AgentConfig


class MarketIntelligence:
    """Market research and competitive analysis"""
    
    def __init__(self, knowledge_base=None):
        self.knowledge_base = knowledge_base
        self.market_data = {}
        
    def analyze_competitors(self, idea: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze competitors for a given idea"""
        competitors = []
        
        # Simulate competitor analysis
        # In production, would query knowledge base
        domain = idea.get('domain', 'general')
        
        competitor_map = {
            'ecommerce': [
                {'name': 'Shopify', 'strengths': ['ease of use', 'ecosystem'], 'weaknesses': ['cost at scale']},
                {'name': 'WooCommerce', 'strengths': ['flexibility', 'open source'], 'weaknesses': ['complexity']},
                {'name': 'BigCommerce', 'strengths': ['enterprise features'], 'weaknesses': ['learning curve']}
            ],
            'saas': [
                {'name': 'Salesforce', 'strengths': ['market leader', 'integrations'], 'weaknesses': ['cost', 'complexity']},
                {'name': 'HubSpot', 'strengths': ['all-in-one', 'user friendly'], 'weaknesses': ['limitations at scale']},
            ]
        }
        
        return competitor_map.get(domain, [])
    
    def estimate_market_size(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate market size and opportunity"""
        return {
            'tam': '$10B',  # Total Addressable Market
            'sam': '$2B',   # Serviceable Addressable Market  
            'som': '$100M', # Serviceable Obtainable Market
            'growth_rate': '15% YoY'
        }


class TechDebtDetector:
    """Identify technical debt zones"""
    
    def scan_codebase(self, path: str) -> List[Dict[str, Any]]:
        """Scan for technical debt indicators"""
        debt_zones = []
        
        # Patterns that indicate tech debt
        debt_patterns = {
            'todo_comments': r'#\s*(TODO|FIXME|HACK)',
            'long_methods': r'def\s+\w+\([^)]*\):[\s\S]{500,}',
            'duplicate_code': r'(.{50,})\n[\s\S]*\1',
            'no_tests': r'(class|def)\s+\w+(?!.*test)',
            'deprecated_apis': r'(deprecated|legacy|old_)',
        }
        
        # In production, would actually scan files
        # For now, return example debt zones
        return [
            {
                'file': 'src/api/users.py',
                'type': 'missing_pagination',
                'severity': 'high',
                'estimated_effort': '2 days',
                'business_impact': 'Will fail at 10K+ users'
            },
            {
                'file': 'src/auth/login.py',
                'type': 'no_rate_limiting',
                'severity': 'critical',
                'estimated_effort': '1 day',
                'business_impact': 'Vulnerable to brute force attacks'
            }
        ]


class EnhancedAnalyst(UnifiedAgent):
    """
    BMAD Analyst enhanced with Gemini Enterprise Architect capabilities
    Mary - Business Analyst specializing in market research, brainstorming, and project briefing
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        # Load BMAD analyst configuration
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.market_intel = MarketIntelligence()
        self.tech_debt_detector = TechDebtDetector()
        
        # Scout functionality
        self.dependency_map = {}
        self.reuse_opportunities = {}
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD analyst configuration"""
        return AgentConfig(
            id="analyst",
            name="Mary",
            title="Business Analyst",
            icon="📊",
            when_to_use="Use for market research, brainstorming, competitive analysis, creating project briefs",
            persona={
                'role': 'Insightful Analyst & Strategic Ideation Partner',
                'style': 'Analytical, inquisitive, creative, facilitative, objective, data-informed',
                'identity': 'Strategic analyst specializing in brainstorming, market research, and project briefing',
                'focus': 'Research planning, ideation facilitation, strategic analysis, actionable insights',
                'core_principles': [
                    'Curiosity-Driven Inquiry',
                    'Objective & Evidence-Based Analysis',
                    'Strategic Contextualization',
                    'Facilitate Clarity & Shared Understanding',
                    'Creative Exploration & Divergent Thinking'
                ]
            },
            commands=[
                {'name': 'brainstorm', 'description': 'Facilitate brainstorming session'},
                {'name': 'create-competitor-analysis', 'description': 'Analyze competitors'},
                {'name': 'create-project-brief', 'description': 'Create project brief'},
                {'name': 'perform-market-research', 'description': 'Conduct market research'},
                {'name': 'scout-analysis', 'description': 'Analyze codebase for reuse'}
            ],
            dependencies={
                'templates': ['project-brief-tmpl.yaml', 'competitor-analysis-tmpl.yaml'],
                'tasks': ['facilitate-brainstorming-session.md', 'create-doc.md'],
                'data': ['bmad-kb.md', 'brainstorming-techniques.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analyst-specific tasks"""
        
        if task == "brainstorm":
            return self.facilitate_brainstorming(context)
        elif task == "create_project_brief":
            return self.create_project_brief(context)
        elif task == "competitor_analysis":
            return self.analyze_competitors(context)
        elif task == "market_research":
            return self.perform_market_research(context)
        elif task == "scout_analysis":
            return self.scout_codebase(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def facilitate_brainstorming(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced brainstorming with GCP service mapping"""
        topic = context.get('topic', 'New Project')
        
        # Load BMAD brainstorming techniques
        techniques = self._load_brainstorming_techniques()
        
        # Generate ideas using various techniques
        ideas = []
        for technique in techniques[:3]:  # Use top 3 techniques
            technique_ideas = self._apply_technique(technique, topic)
            ideas.extend(technique_ideas)
        
        # Enhance each idea with Gemini capabilities
        enhanced_ideas = []
        for idea in ideas:
            enhanced_idea = {
                **idea,
                'gcp_services': self._map_to_gcp_services(idea),
                'competitors': self.market_intel.analyze_competitors(idea),
                'cost_projection': self._estimate_costs(idea),
                'technical_risks': self._assess_technical_risks(idea),
                'scaling_path': self._design_scaling_path(idea)
            }
            enhanced_ideas.append(enhanced_idea)
            
            # Teach about the enhancement
            self.teaching_engine.teach(
                "Service Mapping",
                {
                    'what': f"Mapped idea to GCP services",
                    'why': "Understanding infrastructure needs early prevents costly changes",
                    'how': f"Recommended: {enhanced_idea['gcp_services']}",
                    'example': "Start with Cloud Run, scale to GKE when needed"
                }
            )
        
        return {
            'topic': topic,
            'ideas': enhanced_ideas,
            'techniques_used': [t['name'] for t in techniques[:3]],
            'next_steps': ['Select top ideas', 'Create project brief', 'Validate with stakeholders'],
            'timestamp': datetime.now().isoformat()
        }
    
    def create_project_brief(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive project brief with technical recommendations"""
        
        # Load BMAD template
        template = self.load_bmad_template('project-brief-tmpl.yaml')
        
        # Scout analysis for brownfield projects
        if context.get('existing_codebase'):
            scout_results = self.scout_codebase(context)
            context['scout_analysis'] = scout_results
        
        # Build project brief
        brief = {
            'title': context.get('title', 'New Project'),
            'vision': context.get('vision', ''),
            'objectives': context.get('objectives', []),
            'scope': context.get('scope', {}),
            'stakeholders': context.get('stakeholders', []),
            
            # Enhanced sections
            'market_analysis': {
                'market_size': self.market_intel.estimate_market_size(context),
                'competitors': self.market_intel.analyze_competitors(context),
                'differentiators': self._identify_differentiators(context)
            },
            
            'technical_recommendations': {
                'architecture': self._recommend_architecture(context),
                'tech_stack': self._recommend_tech_stack(context),
                'gcp_services': self._map_to_gcp_services(context),
                'scaling_strategy': self._design_scaling_path(context)
            },
            
            'risk_assessment': {
                'technical_risks': self._assess_technical_risks(context),
                'business_risks': self._assess_business_risks(context),
                'mitigation_strategies': self._create_mitigation_strategies(context)
            },
            
            'cost_analysis': {
                'development_cost': self._estimate_dev_cost(context),
                'infrastructure_cost': self._estimate_infrastructure_cost(context),
                'operational_cost': self._estimate_operational_cost(context),
                'roi_projection': self._project_roi(context)
            }
        }
        
        # Add scout findings if available
        if 'scout_analysis' in context:
            brief['existing_assets'] = {
                'reusable_components': context['scout_analysis']['reuse_opportunities'],
                'technical_debt': context['scout_analysis']['tech_debt'],
                'dependency_risks': context['scout_analysis']['critical_paths']
            }
        
        # Challenge any risky decisions
        if brief['technical_recommendations']['architecture'] == 'monolith':
            challenge = self.challenge_decision(
                "Monolithic architecture",
                {'scale_requirements': context.get('scale_requirements', 'unknown')}
            )
            if challenge:
                brief['architectural_considerations'] = challenge
        
        return brief
    
    def scout_codebase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scout functionality - analyze existing codebase"""
        codebase_path = context.get('codebase_path', '.')
        
        # Scan for reusable components
        self.dependency_map = self.dependency_mapper.analyze(codebase_path)
        
        # Identify technical debt
        tech_debt = self.tech_debt_detector.scan_codebase(codebase_path)
        
        # Find critical paths
        self.dependency_graph.graph = self.dependency_map.get('imports', {})
        critical_paths = self.dependency_graph.find_critical_paths()
        
        # Identify reuse opportunities
        self.reuse_opportunities = self.dependency_graph.get_reuse_opportunities()
        
        # Teach about findings
        if tech_debt:
            self.teaching_engine.teach(
                "Technical Debt Identified",
                {
                    'what': f"Found {len(tech_debt)} technical debt zones",
                    'why': "Technical debt slows development and increases bugs",
                    'how': "Prioritize high-severity items for refactoring",
                    'example': tech_debt[0] if tech_debt else None
                }
            )
        
        return {
            'dependency_map': self.dependency_map,
            'tech_debt': tech_debt,
            'critical_paths': critical_paths,
            'reuse_opportunities': self.reuse_opportunities,
            'summary': {
                'total_files': len(self.dependency_map.get('classes', [])),
                'reusable_components': len(self.reuse_opportunities),
                'debt_items': len(tech_debt),
                'critical_dependencies': len(critical_paths)
            }
        }
    
    def _load_brainstorming_techniques(self) -> List[Dict[str, Any]]:
        """Load BMAD brainstorming techniques"""
        # Would load from .bmad-core/data/brainstorming-techniques.md
        return [
            {'name': 'What If Scenarios', 'type': 'creative'},
            {'name': 'First Principles', 'type': 'analytical'},
            {'name': 'SCAMPER', 'type': 'structured'}
        ]
    
    def _apply_technique(self, technique: Dict[str, Any], topic: str) -> List[Dict[str, Any]]:
        """Apply a brainstorming technique"""
        # Simplified - would implement actual technique logic
        return [
            {
                'idea': f"{topic} - {technique['name']} Idea 1",
                'technique': technique['name'],
                'domain': 'saas'
            }
        ]
    
    def _map_to_gcp_services(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Map requirements to GCP services"""
        services = {}
        
        # Compute recommendations
        if context.get('stateless', True):
            services['compute'] = 'Cloud Run'
        elif context.get('kubernetes'):
            services['compute'] = 'GKE'
        else:
            services['compute'] = 'Compute Engine'
        
        # Data recommendations
        if context.get('realtime'):
            services['database'] = 'Firestore'
        elif context.get('global_consistency'):
            services['database'] = 'Spanner'
        elif context.get('analytics'):
            services['database'] = 'BigQuery'
        else:
            services['database'] = 'Cloud SQL'
        
        # Additional services
        services['storage'] = 'Cloud Storage'
        services['messaging'] = 'Pub/Sub'
        services['monitoring'] = 'Cloud Monitoring'
        
        return services
    
    def _estimate_costs(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Estimate infrastructure costs"""
        services = self._map_to_gcp_services(context)
        
        # Simple cost estimation
        cost_map = {
            'Cloud Run': 50,
            'GKE': 400,
            'Compute Engine': 200,
            'Firestore': 100,
            'Cloud SQL': 150,
            'Spanner': 1000,
            'BigQuery': 200
        }
        
        monthly_cost = sum(cost_map.get(service, 50) for service in services.values())
        
        return {
            'monthly_estimate': f"${monthly_cost}",
            'annual_estimate': f"${monthly_cost * 12}",
            'cost_breakdown': {k: f"${cost_map.get(v, 50)}" for k, v in services.items()}
        }
    
    def _assess_technical_risks(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Assess technical risks"""
        risks = []
        
        if not context.get('pagination'):
            risks.append({
                'risk': 'Missing pagination',
                'impact': 'High - System will fail at scale',
                'mitigation': 'Implement cursor-based pagination'
            })
        
        if not context.get('caching'):
            risks.append({
                'risk': 'No caching strategy',
                'impact': 'Medium - Poor performance under load',
                'mitigation': 'Add Redis/Memorystore caching layer'
            })
        
        return risks
    
    def _recommend_architecture(self, context: Dict[str, Any]) -> str:
        """Recommend architecture pattern"""
        if context.get('microservices'):
            return 'microservices'
        elif context.get('simple'):
            return 'monolith'
        else:
            return 'modular_monolith'
    
    def _recommend_tech_stack(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Recommend technology stack"""
        return {
            'backend': 'Python/FastAPI',
            'frontend': 'React/TypeScript',
            'database': 'PostgreSQL',
            'cache': 'Redis',
            'queue': 'Cloud Tasks'
        }
    
    def _design_scaling_path(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Design scaling journey"""
        return [
            {'phase': 'MVP', 'users': '0-1K', 'architecture': 'Cloud Run + Firestore'},
            {'phase': 'Growth', 'users': '1K-10K', 'architecture': 'Add caching + CDN'},
            {'phase': 'Scale', 'users': '10K-100K', 'architecture': 'Move to GKE + Spanner'},
            {'phase': 'Enterprise', 'users': '100K+', 'architecture': 'Multi-region + Anthos'}
        ]
    
    def _identify_differentiators(self, context: Dict[str, Any]) -> List[str]:
        """Identify key differentiators"""
        return [
            'AI-powered automation',
            'Real-time collaboration',
            'Enterprise-grade security',
            'Seamless scaling'
        ]
    
    def _assess_business_risks(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Assess business risks"""
        return [
            {
                'risk': 'Market competition',
                'impact': 'Medium',
                'mitigation': 'Focus on unique value proposition'
            }
        ]
    
    def _create_mitigation_strategies(self, context: Dict[str, Any]) -> List[str]:
        """Create risk mitigation strategies"""
        return [
            'Implement comprehensive testing',
            'Use progressive rollout',
            'Maintain rollback capability',
            'Regular security audits'
        ]
    
    def _estimate_dev_cost(self, context: Dict[str, Any]) -> str:
        """Estimate development cost"""
        return "$150,000"
    
    def _estimate_infrastructure_cost(self, context: Dict[str, Any]) -> str:
        """Estimate infrastructure cost"""
        return "$1,000/month"
    
    def _estimate_operational_cost(self, context: Dict[str, Any]) -> str:
        """Estimate operational cost"""
        return "$5,000/month"
    
    def _project_roi(self, context: Dict[str, Any]) -> str:
        """Project return on investment"""
        return "Break-even in 6 months, 300% ROI in Year 1"