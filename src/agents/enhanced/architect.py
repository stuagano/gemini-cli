"""
Enhanced Architect Agent
BMAD Architect enhanced with GCP expertise and service surface area intelligence
"""

import yaml
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..unified_agent_base import UnifiedAgent, AgentConfig


class GCPKnowledgeBase:
    """GCP best practices and service knowledge"""
    
    def __init__(self):
        self.services = self._load_service_catalog()
        self.patterns = self._load_architecture_patterns()
        self.decision_trees = self._load_decision_trees()
        
    def _load_service_catalog(self) -> Dict[str, Any]:
        """Load GCP service catalog with details"""
        return {
            'compute': {
                'cloud_run': {
                    'best_for': ['stateless', 'http_apis', 'event_driven'],
                    'pros': ['serverless', 'auto_scaling', 'zero_to_hero'],
                    'cons': ['60min_timeout', 'no_websockets', 'cold_starts'],
                    'cost_model': 'per_request',
                    'scaling': 'automatic',
                    'min_cost': 0,
                    'typical_cost': 50
                },
                'gke': {
                    'best_for': ['microservices', 'stateful', 'complex_networking'],
                    'pros': ['full_kubernetes', 'stateful_support', 'custom_networking'],
                    'cons': ['complexity', 'management_overhead', 'min_cost'],
                    'cost_model': 'per_cluster',
                    'scaling': 'manual_or_auto',
                    'min_cost': 75,
                    'typical_cost': 400
                },
                'gce': {
                    'best_for': ['legacy', 'special_os', 'full_control'],
                    'pros': ['complete_control', 'any_os', 'persistent_disk'],
                    'cons': ['manual_management', 'no_auto_scaling', 'operational_overhead'],
                    'cost_model': 'per_vm',
                    'scaling': 'manual',
                    'min_cost': 25,
                    'typical_cost': 200
                },
                'cloud_functions': {
                    'best_for': ['event_processing', 'webhooks', 'simple_apis'],
                    'pros': ['true_serverless', 'event_triggered', 'simple'],
                    'cons': ['limited_runtime', 'small_payloads', 'cold_starts'],
                    'cost_model': 'per_invocation',
                    'scaling': 'automatic',
                    'min_cost': 0,
                    'typical_cost': 20
                }
            },
            'data': {
                'firestore': {
                    'best_for': ['mobile_apps', 'realtime', 'document_model'],
                    'pros': ['offline_sync', 'realtime_updates', 'global_scale'],
                    'cons': ['query_limitations', 'cost_at_scale', 'no_sql_joins'],
                    'consistency': 'strong',
                    'typical_cost': 100
                },
                'cloud_sql': {
                    'best_for': ['relational', 'existing_sql', 'moderate_scale'],
                    'pros': ['familiar_sql', 'managed_backups', 'read_replicas'],
                    'cons': ['vertical_scaling_limits', 'regional_only', 'maintenance_windows'],
                    'consistency': 'strong',
                    'typical_cost': 150
                },
                'spanner': {
                    'best_for': ['global_consistency', 'financial', 'massive_scale'],
                    'pros': ['global_consistency', 'horizontal_scale', '99.999_sla'],
                    'cons': ['high_cost', 'complexity', 'learning_curve'],
                    'consistency': 'external',
                    'typical_cost': 1000
                },
                'bigquery': {
                    'best_for': ['analytics', 'data_warehouse', 'ml_datasets'],
                    'pros': ['petabyte_scale', 'serverless', 'ml_integration'],
                    'cons': ['not_transactional', 'query_costs', 'latency'],
                    'consistency': 'eventual',
                    'typical_cost': 200
                },
                'bigtable': {
                    'best_for': ['time_series', 'iot', 'high_throughput'],
                    'pros': ['million_qps', 'low_latency', 'hbase_compatible'],
                    'cons': ['no_sql', 'min_cluster_size', 'complex_schema'],
                    'consistency': 'eventual',
                    'typical_cost': 500
                }
            },
            'ml': {
                'vertex_ai_automl': {
                    'best_for': ['quick_prototypes', 'standard_ml', 'no_expertise'],
                    'pros': ['no_ml_expertise', 'quick_results', 'managed'],
                    'cons': ['less_control', 'standard_models', 'cost'],
                    'typical_cost': 500
                },
                'vertex_ai_custom': {
                    'best_for': ['custom_models', 'research', 'special_requirements'],
                    'pros': ['full_control', 'any_framework', 'gpu_support'],
                    'cons': ['requires_expertise', 'complex', 'expensive'],
                    'typical_cost': 2000
                }
            }
        }
    
    def _load_architecture_patterns(self) -> Dict[str, Any]:
        """Load common architecture patterns"""
        return {
            'microservices': {
                'components': ['api_gateway', 'service_mesh', 'message_queue'],
                'gcp_stack': ['cloud_run', 'cloud_endpoints', 'pubsub'],
                'benefits': ['independent_deployment', 'technology_diversity', 'fault_isolation'],
                'challenges': ['complexity', 'network_latency', 'data_consistency']
            },
            'event_driven': {
                'components': ['event_bus', 'event_store', 'processors'],
                'gcp_stack': ['pubsub', 'dataflow', 'cloud_functions'],
                'benefits': ['loose_coupling', 'scalability', 'flexibility'],
                'challenges': ['eventual_consistency', 'debugging', 'ordering']
            },
            'serverless': {
                'components': ['functions', 'managed_services', 'api_gateway'],
                'gcp_stack': ['cloud_run', 'cloud_functions', 'firestore'],
                'benefits': ['no_ops', 'auto_scaling', 'pay_per_use'],
                'challenges': ['vendor_lock', 'cold_starts', 'debugging']
            }
        }
    
    def _load_decision_trees(self) -> Dict[str, Any]:
        """Load service decision trees"""
        return {
            'compute_decision': {
                'question': 'What type of compute workload?',
                'branches': {
                    'stateless_http': {
                        'question': 'Traffic pattern?',
                        'branches': {
                            'variable': 'cloud_run',
                            'constant': 'gke',
                            'bursty': 'cloud_functions'
                        }
                    },
                    'stateful': {
                        'question': 'Orchestration needs?',
                        'branches': {
                            'complex': 'gke',
                            'simple': 'gce'
                        }
                    },
                    'batch': {
                        'question': 'Frequency?',
                        'branches': {
                            'scheduled': 'cloud_scheduler + cloud_run',
                            'continuous': 'dataflow'
                        }
                    }
                }
            },
            'data_decision': {
                'question': 'Data model type?',
                'branches': {
                    'document': {
                        'question': 'Scale needs?',
                        'branches': {
                            'global': 'firestore',
                            'regional': 'cloud_sql_json'
                        }
                    },
                    'relational': {
                        'question': 'Consistency needs?',
                        'branches': {
                            'global_consistency': 'spanner',
                            'regional': 'cloud_sql'
                        }
                    },
                    'analytical': {
                        'question': 'Query pattern?',
                        'branches': {
                            'adhoc': 'bigquery',
                            'streaming': 'bigtable'
                        }
                    }
                }
            }
        }
    
    def recommend_service(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend GCP services based on requirements"""
        recommendations = {}
        
        # Compute recommendation
        if requirements.get('compute'):
            recommendations['compute'] = self._recommend_compute(requirements['compute'])
            
        # Data recommendation
        if requirements.get('data'):
            recommendations['data'] = self._recommend_data(requirements['data'])
            
        # ML recommendation
        if requirements.get('ml'):
            recommendations['ml'] = self._recommend_ml(requirements['ml'])
            
        return recommendations
    
    def _recommend_compute(self, compute_req: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend compute service"""
        scores = {}
        
        for service_name, service_info in self.services['compute'].items():
            score = 0
            matches = []
            
            for requirement in compute_req.get('requirements', []):
                if requirement in service_info['best_for']:
                    score += 10
                    matches.append(requirement)
                    
            scores[service_name] = {
                'score': score,
                'matches': matches,
                'info': service_info
            }
        
        # Sort by score
        sorted_services = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        return {
            'primary': sorted_services[0][0] if sorted_services else 'cloud_run',
            'alternatives': [s[0] for s in sorted_services[1:3]],
            'analysis': scores
        }
    
    def _recommend_data(self, data_req: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend data service"""
        if data_req.get('model') == 'document':
            return {'primary': 'firestore', 'reason': 'Best for document model with real-time'}
        elif data_req.get('global_consistency'):
            return {'primary': 'spanner', 'reason': 'Only option for global consistency'}
        elif data_req.get('analytics'):
            return {'primary': 'bigquery', 'reason': 'Best for analytics workloads'}
        elif data_req.get('time_series'):
            return {'primary': 'bigtable', 'reason': 'Optimized for time-series data'}
        else:
            return {'primary': 'cloud_sql', 'reason': 'Good default for relational data'}
    
    def _recommend_ml(self, ml_req: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend ML service"""
        if ml_req.get('expertise') == 'none':
            return {'primary': 'vertex_ai_automl', 'reason': 'No ML expertise required'}
        else:
            return {'primary': 'vertex_ai_custom', 'reason': 'Full control over model'}


class ServiceSurfaceAreaIntelligence:
    """Complete service decision intelligence"""
    
    def __init__(self, knowledge_base: GCPKnowledgeBase):
        self.kb = knowledge_base
        
    def analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Deep analysis of requirements to recommend services"""
        
        analysis = {
            'compute_analysis': self._analyze_compute_needs(requirements),
            'data_analysis': self._analyze_data_needs(requirements),
            'integration_analysis': self._analyze_integration_needs(requirements),
            'scaling_analysis': self._analyze_scaling_needs(requirements),
            'cost_analysis': self._analyze_cost_implications(requirements),
            'migration_path': self._design_migration_path(requirements)
        }
        
        return analysis
    
    def _analyze_compute_needs(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compute requirements"""
        return {
            'workload_type': self._identify_workload_type(req),
            'scaling_pattern': self._identify_scaling_pattern(req),
            'latency_requirements': req.get('latency', 'standard'),
            'recommendation': self.kb.recommend_service({'compute': req})
        }
    
    def _analyze_data_needs(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data requirements"""
        return {
            'data_model': req.get('data_model', 'relational'),
            'consistency_needs': req.get('consistency', 'eventual'),
            'scale': req.get('scale', 'regional'),
            'access_patterns': req.get('access_patterns', ['read_heavy']),
            'recommendation': self.kb.recommend_service({'data': req})
        }
    
    def _analyze_integration_needs(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze integration requirements"""
        patterns = []
        
        if req.get('microservices'):
            patterns.append('pubsub')
        if req.get('async_processing'):
            patterns.append('cloud_tasks')
        if req.get('workflow'):
            patterns.append('workflows')
            
        return {
            'patterns': patterns,
            'messaging': 'pubsub' if patterns else None,
            'orchestration': 'workflows' if req.get('workflow') else None
        }
    
    def _analyze_scaling_needs(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scaling requirements"""
        initial_users = req.get('initial_users', 1000)
        target_users = req.get('target_users', 10000)
        
        return {
            'initial_scale': initial_users,
            'target_scale': target_users,
            'scaling_factor': target_users / initial_users,
            'auto_scaling_required': target_users > 10000,
            'global_scale_required': target_users > 100000
        }
    
    def _analyze_cost_implications(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cost implications"""
        services = self.kb.recommend_service(req)
        monthly_cost = 0
        
        for category, recommendation in services.items():
            if isinstance(recommendation, dict) and 'primary' in recommendation:
                service_name = recommendation['primary']
                # Get cost from knowledge base
                for svc_category, svc_list in self.kb.services.items():
                    if service_name in svc_list:
                        monthly_cost += svc_list[service_name].get('typical_cost', 100)
                        
        return {
            'estimated_monthly_cost': monthly_cost,
            'estimated_annual_cost': monthly_cost * 12,
            'cost_optimization_tips': self._get_cost_tips(services)
        }
    
    def _design_migration_path(self, req: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Design migration path from current to target architecture"""
        return [
            {
                'phase': 'MVP',
                'timeline': '0-3 months',
                'architecture': 'Monolith on Cloud Run',
                'services': ['cloud_run', 'cloud_sql', 'cloud_storage'],
                'cost': '$200/month'
            },
            {
                'phase': 'Growth',
                'timeline': '3-6 months',
                'architecture': 'Modular monolith with caching',
                'services': ['cloud_run', 'memorystore', 'cloud_cdn'],
                'cost': '$500/month'
            },
            {
                'phase': 'Scale',
                'timeline': '6-12 months',
                'architecture': 'Microservices on GKE',
                'services': ['gke', 'pubsub', 'spanner'],
                'cost': '$2000/month'
            }
        ]
    
    def _identify_workload_type(self, req: Dict[str, Any]) -> str:
        if req.get('stateless') and req.get('http'):
            return 'stateless_http'
        elif req.get('stateful'):
            return 'stateful'
        elif req.get('batch'):
            return 'batch'
        else:
            return 'general'
    
    def _identify_scaling_pattern(self, req: Dict[str, Any]) -> str:
        if req.get('traffic_pattern') == 'spiky':
            return 'auto_scaling_critical'
        elif req.get('traffic_pattern') == 'steady':
            return 'predictable_scaling'
        else:
            return 'variable_scaling'
    
    def _get_cost_tips(self, services: Dict[str, Any]) -> List[str]:
        tips = []
        
        if 'cloud_run' in str(services):
            tips.append('Cloud Run scales to zero - no cost when idle')
        if 'gke' in str(services):
            tips.append('Use GKE Autopilot for reduced management overhead')
        if 'spanner' in str(services):
            tips.append('Start with minimum nodes and scale as needed')
            
        return tips


class EnhancedArchitect(UnifiedAgent):
    """
    BMAD Architect enhanced with GCP expertise and service intelligence
    Archie - Solution Architect designing scalable, secure systems
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.gcp_kb = GCPKnowledgeBase()
        self.service_intelligence = ServiceSurfaceAreaIntelligence(self.gcp_kb)
        
        # Architecture components
        self.architecture_decisions = []
        self.trade_offs = []
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD architect configuration"""
        return AgentConfig(
            id="architect",
            name="Archie",
            title="Solution Architect",
            icon="🏗️",
            when_to_use="Use for system design, architecture decisions, service selection, scaling strategies",
            persona={
                'role': 'Principal Solution Architect & Technical Visionary',
                'style': 'Strategic, analytical, forward-thinking, pragmatic',
                'identity': 'Expert architect designing scalable, maintainable systems',
                'focus': 'System design, scalability, security, best practices',
                'core_principles': [
                    'Design for scale from day one',
                    'Security and compliance by design',
                    'Choose boring technology',
                    'Optimize for maintainability',
                    'Plan for failure'
                ]
            },
            commands=[
                {'name': 'design-architecture', 'description': 'Design system architecture'},
                {'name': 'select-services', 'description': 'Select appropriate services'},
                {'name': 'review-architecture', 'description': 'Review and improve architecture'},
                {'name': 'create-adr', 'description': 'Create Architecture Decision Record'},
                {'name': 'scaling-analysis', 'description': 'Analyze scaling requirements'}
            ],
            dependencies={
                'templates': ['architecture-tmpl.yaml', 'adr-tmpl.yaml'],
                'data': ['gcp-best-practices.md', 'architecture-patterns.md'],
                'checklists': ['architecture-review-checklist.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute architect-specific tasks"""
        
        if task == "design_architecture":
            return self.design_architecture(context)
        elif task == "select_services":
            return self.select_services(context)
        elif task == "review_architecture":
            return self.review_architecture(context)
        elif task == "create_adr":
            return self.create_adr(context)
        elif task == "scaling_analysis":
            return self.analyze_scaling(context)
        elif task == "provide_design_recommendations":
            return self.provide_design_recommendations(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def design_architecture(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design comprehensive system architecture"""
        
        prd = context.get('prd', {})
        requirements = self._extract_requirements(prd)
        
        # Analyze requirements deeply
        analysis = self.service_intelligence.analyze_requirements(requirements)
        
        # Design architecture
        architecture = {
            'title': f"Architecture for {prd.get('title', 'System')}",
            'version': '1.0',
            'created_date': datetime.now().isoformat(),
            'architect': 'Architect Agent (Archie)',
            
            # High-level design
            'overview': {
                'pattern': self._select_architecture_pattern(requirements),
                'style': self._select_architecture_style(requirements),
                'principles': self._define_principles(requirements)
            },
            
            # Service architecture with intelligence
            'services': {
                'compute': self._design_compute_architecture(analysis['compute_analysis']),
                'data': self._design_data_architecture(analysis['data_analysis']),
                'integration': self._design_integration_architecture(analysis['integration_analysis']),
                'security': self._design_security_architecture(requirements)
            },
            
            # Scaling design
            'scaling_strategy': self._design_scaling_strategy(analysis['scaling_analysis']),
            
            # Cost optimization
            'cost_optimization': analysis['cost_analysis'],
            
            # Migration path
            'migration_path': analysis['migration_path'],
            
            # Architecture decisions
            'key_decisions': self._document_key_decisions(analysis),
            
            # Trade-offs
            'trade_offs': self._analyze_trade_offs(analysis),
            
            # Risks and mitigations
            'risks': self._identify_architectural_risks(analysis),
            
            # Non-functional requirements
            'nfrs': self._address_nfrs(requirements),
            
            # Diagrams (descriptions)
            'diagrams': self._create_diagram_specs(architecture)
        }
        
        # Challenge risky decisions
        self._challenge_architecture_decisions(architecture)
        
        # Teach about architecture
        self._teach_architecture_concepts(architecture, analysis)
        
        return architecture
    
    def select_services(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligent service selection with teaching"""
        
        requirements = context.get('requirements', {})
        
        # Get recommendations
        recommendations = self.gcp_kb.recommend_service(requirements)
        
        # Enhance with detailed comparison
        detailed_comparison = {}
        
        for category, recommendation in recommendations.items():
            if isinstance(recommendation, dict) and 'primary' in recommendation:
                detailed_comparison[category] = self._create_service_comparison(
                    category,
                    recommendation,
                    requirements
                )
        
        # Create decision matrix
        decision_matrix = self._create_decision_matrix(detailed_comparison)
        
        # Teach about service selection
        self.teaching_engine.teach(
            "Service Selection",
            {
                'what': f"Selected {recommendations.get('compute', {}).get('primary', 'services')} for compute",
                'why': "Based on stateless HTTP workload with variable traffic",
                'how': "Cloud Run provides serverless scaling with zero cost when idle",
                'example': "Spotify uses similar architecture for microservices"
            }
        )
        
        return {
            'recommendations': recommendations,
            'detailed_comparison': detailed_comparison,
            'decision_matrix': decision_matrix,
            'implementation_guide': self._create_implementation_guide(recommendations)
        }
    
    def review_architecture(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review architecture for issues and improvements"""
        
        architecture = context.get('architecture', {})
        
        review = {
            'overall_score': 0,
            'categories': {},
            'issues': [],
            'improvements': [],
            'compliance': {}
        }
        
        # Review scalability
        scalability_review = self._review_scalability(architecture)
        review['categories']['scalability'] = scalability_review
        
        # Review security
        security_review = self._review_security(architecture)
        review['categories']['security'] = security_review
        
        # Review reliability
        reliability_review = self._review_reliability(architecture)
        review['categories']['reliability'] = reliability_review
        
        # Review cost optimization
        cost_review = self._review_cost_optimization(architecture)
        review['categories']['cost'] = cost_review
        
        # Check for anti-patterns
        anti_patterns = self._detect_anti_patterns(architecture)
        if anti_patterns:
            review['issues'].extend(anti_patterns)
        
        # Suggest improvements
        improvements = self._suggest_improvements(architecture, review)
        review['improvements'] = improvements
        
        # Calculate overall score
        scores = [cat.get('score', 0) for cat in review['categories'].values()]
        review['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        # Generate action items
        review['action_items'] = self._generate_action_items(review)
        
        return review
    
    def create_adr(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create Architecture Decision Record"""
        
        decision = context.get('decision', {})
        
        adr = {
            'id': f"ADR-{len(self.architecture_decisions) + 1:03d}",
            'title': decision.get('title', 'Architecture Decision'),
            'date': datetime.now().isoformat(),
            'status': 'Proposed',
            
            # Context
            'context': decision.get('context', ''),
            
            # Decision
            'decision': decision.get('decision', ''),
            
            # Alternatives considered
            'alternatives': self._analyze_alternatives(decision),
            
            # Consequences
            'consequences': {
                'positive': decision.get('pros', []),
                'negative': decision.get('cons', []),
                'risks': self._identify_decision_risks(decision)
            },
            
            # Trade-offs
            'trade_offs': self._document_trade_offs(decision),
            
            # Implementation notes
            'implementation': decision.get('implementation', ''),
            
            # References
            'references': self._gather_references(decision)
        }
        
        self.architecture_decisions.append(adr)
        
        # Teach about the decision
        self.teaching_engine.teach(
            "Architecture Decision",
            {
                'what': adr['title'],
                'why': adr['context'],
                'how': adr['decision'],
                'tradeoffs': adr['trade_offs']
            }
        )
        
        return adr
    
    def analyze_scaling(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deep scaling analysis with predictions"""
        
        current_load = context.get('current_load', {})
        expected_growth = context.get('growth_rate', 2.0)  # 2x per year
        
        analysis = {
            'current_state': {
                'users': current_load.get('users', 1000),
                'rps': current_load.get('rps', 100),
                'data_size': current_load.get('data_gb', 10)
            },
            
            # Scaling predictions
            'predictions': self._predict_scaling_needs(current_load, expected_growth),
            
            # Bottleneck analysis
            'bottlenecks': self._identify_bottlenecks(context),
            
            # Scaling strategy
            'strategy': self._create_scaling_strategy(context),
            
            # Service evolution
            'service_evolution': self._plan_service_evolution(current_load, expected_growth),
            
            # Cost projection
            'cost_projection': self._project_scaling_costs(current_load, expected_growth),
            
            # Action plan
            'action_plan': self._create_scaling_action_plan(context)
        }
        
        # Detect scaling issues
        issues = self._detect_scaling_issues(context)
        if issues:
            analysis['critical_issues'] = issues
            self._teach_scaling_issues(issues)
        
        return analysis

    def provide_design_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide high-level design recommendations based on project context."""
        
        # For this task, we'll analyze the project root to get a high-level overview.
        # In a real scenario, this would involve a more sophisticated analysis of the codebase.
        project_path = context.get('project_path', '.')
        files = list(Path(project_path).glob('**/*'))
        
        # Simple heuristics to guess the project type
        requirements = {}
        if any(f.name == 'package.json' for f in files):
            requirements['compute'] = {'requirements': ['stateless', 'http_apis']}
            requirements['data'] = {'model': 'document'}
        elif any(f.name == 'requirements.txt' for f in files):
            requirements['compute'] = {'requirements': ['batch']}
            requirements['data'] = {'analytics': True}
        
        if not requirements:
            return {'error': 'Could not determine project type to provide recommendations.'}

        # Leverage the existing intelligence to get recommendations
        analysis = self.service_intelligence.analyze_requirements(requirements)
        
        recommendations = {
            'summary': 'Based on a high-level analysis of your project, here are some initial design recommendations.',
            'compute': analysis.get('compute_analysis', {}).get('recommendation'),
            'data': analysis.get('data_analysis', {}).get('recommendation'),
            'cost_implications': analysis.get('cost_analysis'),
            'migration_path': analysis.get('migration_path')
        }
        
        return recommendations
    
    def _extract_requirements(self, prd: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements from PRD"""
        return {
            'functional': prd.get('functional_requirements', []),
            'nfr': prd.get('non_functional_requirements', []),
            'scale': prd.get('technical_constraints', {}).get('scaling_requirements', {}),
            'security': prd.get('technical_constraints', {}).get('security_requirements', [])
        }
    
    def _select_architecture_pattern(self, requirements: Dict[str, Any]) -> str:
        """Select appropriate architecture pattern"""
        if len(requirements.get('functional', [])) > 20:
            return 'microservices'
        elif requirements.get('scale', {}).get('global'):
            return 'distributed'
        else:
            return 'modular_monolith'
    
    def _select_architecture_style(self, requirements: Dict[str, Any]) -> str:
        """Select architecture style"""
        if 'event' in str(requirements).lower():
            return 'event_driven'
        elif 'api' in str(requirements).lower():
            return 'api_first'
        else:
            return 'layered'
    
    def _define_principles(self, requirements: Dict[str, Any]) -> List[str]:
        """Define architecture principles"""
        return [
            'Cloud-native from the start',
            'API-first design',
            'Security by design',
            'Observable by default',
            'Cost-conscious decisions',
            'Embrace managed services'
        ]
    
    def _design_compute_architecture(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Design compute layer"""
        recommendation = analysis['recommendation']
        
        return {
            'primary_service': recommendation['compute']['primary'],
            'deployment_model': 'containerized',
            'orchestration': 'cloud_run' if recommendation['compute']['primary'] == 'cloud_run' else 'kubernetes',
            'scaling': {
                'min_instances': 1,
                'max_instances': 100,
                'target_cpu': 60,
                'target_concurrency': 80
            },
            'regions': ['us-central1', 'us-east1'],
            'load_balancing': 'global_https_lb'
        }
    
    def _design_data_architecture(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Design data layer"""
        return {
            'primary_database': analysis['recommendation']['data']['primary'],
            'caching': 'memorystore_redis',
            'object_storage': 'cloud_storage',
            'data_pipeline': 'dataflow' if analysis.get('streaming') else None,
            'backup_strategy': 'automated_daily',
            'replication': 'multi_region' if analysis.get('scale') == 'global' else 'regional'
        }
    
    def _design_integration_architecture(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Design integration layer"""
        return {
            'messaging': analysis.get('messaging', 'pubsub'),
            'api_gateway': 'cloud_endpoints',
            'service_mesh': 'istio' if analysis.get('microservices') else None,
            'workflow': analysis.get('orchestration', 'workflows')
        }
    
    def _design_security_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Design security architecture"""
        return {
            'authentication': 'identity_platform',
            'authorization': 'iam_and_rbac',
            'network_security': {
                'vpc': 'custom_vpc',
                'firewall': 'cloud_armor',
                'private_access': 'private_google_access'
            },
            'data_security': {
                'encryption_at_rest': 'cmek',
                'encryption_in_transit': 'tls_1_3',
                'secrets_management': 'secret_manager'
            },
            'compliance': requirements.get('compliance', [])
        }
    
    def _design_scaling_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Design scaling strategy"""
        return {
            'horizontal_scaling': {
                'enabled': True,
                'min': 1,
                'max': 100 if analysis['target_scale'] < 100000 else 1000
            },
            'vertical_scaling': {
                'enabled': False,
                'reason': 'Horizontal scaling preferred for resilience'
            },
            'auto_scaling_triggers': {
                'cpu': 60,
                'memory': 70,
                'request_rate': 1000,
                'custom_metrics': ['queue_depth', 'response_time']
            },
            'scaling_schedule': {
                'peak_hours': '09:00-18:00',
                'scale_up': 2.0,
                'scale_down': 0.5
            }
        }
    
    def _document_key_decisions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Document key architecture decisions"""
        decisions = []
        
        # Compute decision
        compute = analysis['compute_analysis']['recommendation']['compute']
        decisions.append({
            'decision': f"Use {compute['primary']} for compute",
            'rationale': f"Best fit for {analysis['compute_analysis']['workload_type']} workloads",
            'alternatives': compute.get('alternatives', []),
            'trade_offs': 'Serverless simplicity vs control'
        })
        
        # Data decision
        data = analysis['data_analysis']['recommendation']['data']
        decisions.append({
            'decision': f"Use {data['primary']} for data storage",
            'rationale': data.get('reason', 'Best fit for requirements'),
            'alternatives': ['cloud_sql', 'spanner', 'firestore'],
            'trade_offs': 'Consistency vs cost'
        })
        
        return decisions
    
    def _analyze_trade_offs(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze architecture trade-offs"""
        return [
            {
                'aspect': 'Consistency vs Availability',
                'choice': 'Availability',
                'rationale': 'User experience prioritized over strict consistency',
                'impact': 'Eventual consistency for non-critical data'
            },
            {
                'aspect': 'Cost vs Performance',
                'choice': 'Balanced',
                'rationale': 'Optimize for cost with acceptable performance',
                'impact': 'Use caching and CDN to reduce compute costs'
            },
            {
                'aspect': 'Simplicity vs Flexibility',
                'choice': 'Simplicity',
                'rationale': 'Reduce operational complexity',
                'impact': 'Use managed services even with some limitations'
            }
        ]
    
    def _identify_architectural_risks(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify architectural risks"""
        risks = []
        
        # Scaling risks
        if analysis['scaling_analysis']['scaling_factor'] > 10:
            risks.append({
                'risk': 'Rapid scaling requirements',
                'impact': 'High',
                'probability': 'Medium',
                'mitigation': 'Design for 10x growth, implement auto-scaling early'
            })
        
        # Cost risks
        if analysis['cost_analysis']['estimated_monthly_cost'] > 5000:
            risks.append({
                'risk': 'High infrastructure costs',
                'impact': 'Medium',
                'probability': 'High',
                'mitigation': 'Implement cost monitoring and optimization from day 1'
            })
        
        # Complexity risks
        if 'microservices' in str(analysis):
            risks.append({
                'risk': 'Microservices complexity',
                'impact': 'Medium',
                'probability': 'High',
                'mitigation': 'Start with modular monolith, evolve to microservices'
            })
        
        return risks
    
    def _address_nfrs(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Address non-functional requirements"""
        return {
            'performance': 'Achieve <100ms p99 latency through caching and CDN',
            'availability': 'Multi-region deployment for 99.99% uptime',
            'security': 'Defense in depth with multiple security layers',
            'scalability': 'Horizontal scaling with auto-scaling policies',
            'maintainability': 'Microservices with clear boundaries',
            'observability': 'Full stack monitoring with tracing and logging'
        }
    
    def _create_diagram_specs(self, architecture: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create specifications for architecture diagrams"""
        return [
            {
                'type': 'system_context',
                'description': 'High-level system context showing external actors',
                'components': ['users', 'external_systems', 'main_system']
            },
            {
                'type': 'container',
                'description': 'Container diagram showing major components',
                'components': ['frontend', 'api', 'database', 'cache', 'queue']
            },
            {
                'type': 'deployment',
                'description': 'Deployment diagram showing GCP services',
                'components': list(architecture.get('services', {}).keys())
            }
        ]
    
    def _challenge_architecture_decisions(self, architecture: Dict[str, Any]):
        """Challenge potentially problematic decisions"""
        
        # Check for monolith at scale
        if architecture['overview']['pattern'] == 'monolith' and \
           architecture.get('scaling_strategy', {}).get('horizontal_scaling', {}).get('max', 0) > 10:
            
            challenge = self.challenge_decision(
                "Monolithic architecture with high scaling requirements",
                {
                    'pattern': architecture['overview']['pattern'],
                    'scale': architecture['scaling_strategy']
                }
            )
            if challenge:
                architecture['challenges'] = [challenge]
        
        # Check for expensive services without justification
        if 'spanner' in str(architecture) and \
           architecture.get('cost_optimization', {}).get('estimated_monthly_cost', 0) < 10000:
            
            self.teaching_engine.teach(
                "Cost-Service Mismatch",
                {
                    'what': "Spanner selected but budget seems limited",
                    'why': "Spanner starts at $1000/month minimum",
                    'how': "Consider Cloud SQL for regional needs",
                    'example': "Only use Spanner for global consistency requirements"
                }
            )
    
    def _teach_architecture_concepts(self, architecture: Dict[str, Any], analysis: Dict[str, Any]):
        """Teach architectural concepts"""
        
        # Teach about selected pattern
        pattern = architecture['overview']['pattern']
        self.teaching_engine.teach(
            f"{pattern.title()} Architecture",
            {
                'what': f"Designed {pattern} architecture",
                'why': self.gcp_kb.patterns.get(pattern, {}).get('benefits', []),
                'how': f"Implement using {self.gcp_kb.patterns.get(pattern, {}).get('gcp_stack', [])}",
                'tradeoffs': self.gcp_kb.patterns.get(pattern, {}).get('challenges', [])
            }
        )
        
        # Teach about scaling
        if analysis.get('scaling_analysis', {}).get('auto_scaling_required'):
            self.teaching_engine.teach(
                "Auto-scaling Design",
                {
                    'what': "Implemented auto-scaling strategy",
                    'why': "Handle 10x traffic spikes without manual intervention",
                    'how': "Cloud Run auto-scales from 0 to 1000 instances",
                    'example': "Set min instances to avoid cold starts"
                }
            )
    
    def _create_service_comparison(self, category: str, recommendation: Dict[str, Any], 
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed service comparison"""
        
        comparison = {
            'category': category,
            'recommendation': recommendation['primary'],
            'alternatives': recommendation.get('alternatives', []),
            'comparison_matrix': {}
        }
        
        # Get all services in category
        services = self.gcp_kb.services.get(category, {})
        
        for service_name, service_info in services.items():
            comparison['comparison_matrix'][service_name] = {
                'pros': service_info.get('pros', []),
                'cons': service_info.get('cons', []),
                'cost': service_info.get('typical_cost', 'Unknown'),
                'best_for': service_info.get('best_for', []),
                'match_score': self._calculate_match_score(service_info, requirements)
            }
        
        return comparison
    
    def _create_decision_matrix(self, detailed_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Create decision matrix for service selection"""
        
        matrix = {
            'criteria': ['cost', 'scalability', 'complexity', 'vendor_lock', 'features'],
            'weights': {'cost': 0.3, 'scalability': 0.3, 'complexity': 0.2, 
                       'vendor_lock': 0.1, 'features': 0.1},
            'scores': {}
        }
        
        # Score each service
        for category, comparison in detailed_comparison.items():
            if 'comparison_matrix' in comparison:
                for service, info in comparison['comparison_matrix'].items():
                    matrix['scores'][service] = {
                        'cost': 5 - (info['cost'] / 500) if isinstance(info['cost'], (int, float)) else 3,
                        'scalability': 5 if 'auto' in str(info.get('pros', [])) else 3,
                        'complexity': 5 if 'simple' in str(info.get('pros', [])) else 3,
                        'vendor_lock': 3,  # All GCP services have some lock-in
                        'features': info.get('match_score', 3)
                    }
        
        return matrix
    
    def _create_implementation_guide(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation guide for recommended services"""
        
        guide = {
            'prerequisites': [
                'GCP project created',
                'Billing enabled',
                'APIs enabled',
                'IAM roles configured'
            ],
            'implementation_steps': [],
            'terraform_modules': [],
            'monitoring_setup': []
        }
        
        # Add steps for each recommended service
        for category, recommendation in recommendations.items():
            if isinstance(recommendation, dict) and 'primary' in recommendation:
                service = recommendation['primary']
                guide['implementation_steps'].append({
                    'service': service,
                    'steps': self._get_implementation_steps(service),
                    'estimated_time': '2-4 hours'
                })
                guide['terraform_modules'].append(f"google_{service}")
        
        return guide
    
    def _get_implementation_steps(self, service: str) -> List[str]:
        """Get implementation steps for a service"""
        steps_map = {
            'cloud_run': [
                'Containerize application',
                'Push to Container Registry',
                'Deploy to Cloud Run',
                'Configure domain mapping',
                'Set up monitoring'
            ],
            'firestore': [
                'Create Firestore database',
                'Design document structure',
                'Set up security rules',
                'Create indexes',
                'Configure backups'
            ]
        }
        return steps_map.get(service, ['Configure service', 'Test functionality'])
    
    def _calculate_match_score(self, service_info: Dict[str, Any], 
                               requirements: Dict[str, Any]) -> float:
        """Calculate how well service matches requirements"""
        score = 0
        max_score = 0
        
        for req_key, req_value in requirements.items():
            max_score += 1
            if req_key in service_info.get('best_for', []):
                score += 1
            elif req_value in str(service_info.get('pros', [])):
                score += 0.5
                
        return (score / max_score * 5) if max_score > 0 else 3
    
    def _review_scalability(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Review scalability aspects"""
        score = 0
        issues = []
        
        # Check for horizontal scaling
        if architecture.get('scaling_strategy', {}).get('horizontal_scaling', {}).get('enabled'):
            score += 25
        else:
            issues.append('No horizontal scaling configured')
        
        # Check for auto-scaling
        if architecture.get('scaling_strategy', {}).get('auto_scaling_triggers'):
            score += 25
        else:
            issues.append('No auto-scaling triggers defined')
        
        # Check for caching
        if 'cache' in str(architecture).lower() or 'redis' in str(architecture).lower():
            score += 25
        else:
            issues.append('No caching layer defined')
        
        # Check for CDN
        if 'cdn' in str(architecture).lower():
            score += 25
        else:
            issues.append('No CDN for static content')
        
        return {
            'score': score,
            'issues': issues,
            'recommendations': [
                'Implement horizontal auto-scaling',
                'Add caching layer with Redis',
                'Use Cloud CDN for global content delivery'
            ] if score < 75 else []
        }
    
    def _review_security(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Review security aspects"""
        score = 0
        issues = []
        
        security = architecture.get('services', {}).get('security', {})
        
        # Check authentication
        if security.get('authentication'):
            score += 25
        else:
            issues.append('No authentication mechanism defined')
        
        # Check encryption
        if security.get('data_security', {}).get('encryption_at_rest'):
            score += 25
        else:
            issues.append('No encryption at rest specified')
        
        # Check network security
        if security.get('network_security', {}).get('firewall'):
            score += 25
        else:
            issues.append('No firewall configuration')
        
        # Check secrets management
        if 'secret_manager' in str(security):
            score += 25
        else:
            issues.append('No secrets management solution')
        
        return {
            'score': score,
            'issues': issues,
            'recommendations': [
                'Implement OAuth 2.0 with Identity Platform',
                'Enable CMEK for sensitive data',
                'Configure Cloud Armor for DDoS protection'
            ] if score < 75 else []
        }
    
    def _review_reliability(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Review reliability aspects"""
        score = 0
        issues = []
        
        # Check for multi-region
        if 'multi' in str(architecture.get('services', {})).lower():
            score += 33
        else:
            issues.append('Single region deployment')
        
        # Check for backups
        if 'backup' in str(architecture).lower():
            score += 33
        else:
            issues.append('No backup strategy defined')
        
        # Check for monitoring
        if 'monitoring' in str(architecture).lower():
            score += 34
        else:
            issues.append('No monitoring strategy')
        
        return {
            'score': score,
            'issues': issues,
            'recommendations': [
                'Implement multi-region deployment',
                'Set up automated backups',
                'Configure comprehensive monitoring'
            ] if score < 75 else []
        }
    
    def _review_cost_optimization(self, architecture: Dict[str, Any]) -> Dict[str, Any]:
        """Review cost optimization"""
        score = 0
        issues = []
        
        # Check for serverless usage
        if 'cloud_run' in str(architecture).lower() or 'functions' in str(architecture).lower():
            score += 50
        else:
            issues.append('Not leveraging serverless for cost optimization')
        
        # Check for appropriate service selection
        if 'spanner' in str(architecture).lower():
            issues.append('Spanner may be overkill - consider Cloud SQL')
            score -= 25
        
        # Check for resource limits
        if architecture.get('scaling_strategy', {}).get('horizontal_scaling', {}).get('max'):
            score += 25
        else:
            issues.append('No maximum scaling limits defined')
        
        # Check for scheduled scaling
        if architecture.get('scaling_strategy', {}).get('scaling_schedule'):
            score += 25
        else:
            issues.append('No scheduled scaling for predictable traffic')
        
        return {
            'score': max(0, score),
            'issues': issues,
            'recommendations': [
                'Use Cloud Run for variable workloads',
                'Implement scheduled scaling',
                'Set resource quotas and limits'
            ] if score < 50 else []
        }
    
    def _detect_anti_patterns(self, architecture: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect architectural anti-patterns"""
        anti_patterns = []
        
        # Check for distributed monolith
        if architecture.get('overview', {}).get('pattern') == 'microservices' and \
           len(architecture.get('services', {})) < 3:
            anti_patterns.append({
                'pattern': 'Distributed Monolith',
                'description': 'Microservices architecture with too few services',
                'impact': 'Complexity without benefits',
                'fix': 'Start with modular monolith'
            })
        
        # Check for synchronous microservices
        if 'microservices' in str(architecture) and \
           'pubsub' not in str(architecture).lower():
            anti_patterns.append({
                'pattern': 'Synchronous Microservices',
                'description': 'Microservices without async messaging',
                'impact': 'Tight coupling and cascading failures',
                'fix': 'Implement event-driven communication with Pub/Sub'
            })
        
        return anti_patterns
    
    def _suggest_improvements(self, architecture: Dict[str, Any], 
                             review: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest architecture improvements"""
        improvements = []
        
        # Based on review scores
        for category, review_data in review['categories'].items():
            if review_data.get('score', 0) < 75:
                improvements.extend([
                    {
                        'category': category,
                        'improvement': rec,
                        'priority': 'High' if review_data['score'] < 50 else 'Medium',
                        'effort': '1 week'
                    }
                    for rec in review_data.get('recommendations', [])
                ])
        
        return improvements
    
    def _generate_action_items(self, review: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable items from review"""
        action_items = []
        priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
        
        # Convert improvements to action items
        for improvement in review.get('improvements', []):
            action_items.append({
                'action': improvement['improvement'],
                'priority': improvement.get('priority', 'Medium'),
                'category': improvement['category'],
                'effort': improvement.get('effort', 'Unknown')
            })
        
        # Sort by priority
        action_items.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return action_items
    
    def _analyze_alternatives(self, decision: Dict[str, Any]) -> List[Dict[str, str]]:
        """Analyze alternative solutions"""
        alternatives = []
        
        # Get alternatives from decision context
        for alt in decision.get('alternatives', []):
            alternatives.append({
                'option': alt,
                'pros': self._get_alternative_pros(alt),
                'cons': self._get_alternative_cons(alt),
                'when_to_use': self._get_alternative_use_case(alt)
            })
        
        return alternatives
    
    def _get_alternative_pros(self, alternative: str) -> List[str]:
        """Get pros for alternative"""
        pros_map = {
            'kubernetes': ['Full control', 'Rich ecosystem', 'Portable'],
            'cloud_sql': ['Familiar SQL', 'Lower cost', 'Simple'],
            'monolith': ['Simple deployment', 'Easy debugging', 'Lower complexity']
        }
        return pros_map.get(alternative.lower(), ['To be analyzed'])
    
    def _get_alternative_cons(self, alternative: str) -> List[str]:
        """Get cons for alternative"""
        cons_map = {
            'kubernetes': ['Complex', 'Operational overhead', 'Expensive'],
            'cloud_sql': ['Regional only', 'Scaling limits', 'Maintenance windows'],
            'monolith': ['Scaling challenges', 'Single point of failure', 'Technology lock-in']
        }
        return cons_map.get(alternative.lower(), ['To be analyzed'])
    
    def _get_alternative_use_case(self, alternative: str) -> str:
        """Get use case for alternative"""
        use_cases = {
            'kubernetes': 'When you need full orchestration control',
            'cloud_sql': 'For simple relational data with regional scope',
            'monolith': 'For MVPs and simple applications'
        }
        return use_cases.get(alternative.lower(), 'Depends on specific requirements')
    
    def _identify_decision_risks(self, decision: Dict[str, Any]) -> List[str]:
        """Identify risks in architecture decision"""
        risks = []
        
        decision_text = str(decision).lower()
        
        if 'microservices' in decision_text:
            risks.append('Increased operational complexity')
        if 'spanner' in decision_text:
            risks.append('High minimum cost threshold')
        if 'monolith' in decision_text and 'scale' in decision_text:
            risks.append('Scaling limitations')
            
        return risks
    
    def _document_trade_offs(self, decision: Dict[str, Any]) -> List[Dict[str, str]]:
        """Document trade-offs for decision"""
        return [
            {
                'giving_up': 'Simplicity',
                'gaining': 'Scalability',
                'worth_it_when': 'Growth is priority'
            },
            {
                'giving_up': 'Control',
                'gaining': 'Reduced operations',
                'worth_it_when': 'Team is small'
            }
        ]
    
    def _gather_references(self, decision: Dict[str, Any]) -> List[str]:
        """Gather references for decision"""
        return [
            'https://cloud.google.com/architecture/framework',
            'https://cloud.google.com/blog/topics/developers-practitioners',
            'Internal architecture guidelines',
            'Similar system case studies'
        ]
    
    def _predict_scaling_needs(self, current_load: Dict[str, Any], 
                               growth_rate: float) -> Dict[str, Any]:
        """Predict future scaling needs"""
        predictions = {}
        
        for period in [3, 6, 12, 24]:  # months
            multiplier = (1 + growth_rate) ** (period / 12)
            predictions[f'{period}_months'] = {
                'users': int(current_load.get('users', 1000) * multiplier),
                'rps': int(current_load.get('rps', 100) * multiplier),
                'data_gb': int(current_load.get('data_gb', 10) * multiplier),
                'recommended_architecture': self._get_architecture_for_scale(
                    int(current_load.get('users', 1000) * multiplier)
                )
            }
        
        return predictions
    
    def _get_architecture_for_scale(self, users: int) -> str:
        """Get recommended architecture for user scale"""
        if users < 10000:
            return 'Monolith on Cloud Run'
        elif users < 100000:
            return 'Modular services on Cloud Run'
        elif users < 1000000:
            return 'Microservices on GKE'
        else:
            return 'Multi-region microservices with global load balancing'
    
    def _identify_bottlenecks(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify scaling bottlenecks"""
        bottlenecks = []
        
        # Database bottlenecks
        if not context.get('database_sharding'):
            bottlenecks.append({
                'component': 'Database',
                'issue': 'No sharding strategy',
                'impact': 'Will hit vertical scaling limits',
                'solution': 'Implement sharding or move to Spanner'
            })
        
        # API bottlenecks  
        if not context.get('rate_limiting'):
            bottlenecks.append({
                'component': 'API',
                'issue': 'No rate limiting',
                'impact': 'Vulnerable to abuse and overload',
                'solution': 'Implement rate limiting with Cloud Endpoints'
            })
        
        return bottlenecks
    
    def _create_scaling_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive scaling strategy"""
        return {
            'horizontal_scaling': {
                'compute': 'Auto-scale instances based on CPU/memory',
                'database': 'Read replicas and sharding',
                'cache': 'Distributed cache with Redis cluster'
            },
            'vertical_scaling': {
                'when_needed': 'Temporary for specific bottlenecks',
                'limit': 'Move to horizontal before hitting limits'
            },
            'geographic_scaling': {
                'cdn': 'Cloud CDN for static content',
                'multi_region': 'Deploy to multiple regions at 100K users',
                'global_lb': 'Global load balancing for traffic distribution'
            }
        }
    
    def _plan_service_evolution(self, current_load: Dict[str, Any], 
                                growth_rate: float) -> List[Dict[str, str]]:
        """Plan service evolution path"""
        return [
            {
                'phase': 'Current',
                'services': 'Cloud Run + Cloud SQL',
                'changes_needed': 'None'
            },
            {
                'phase': '10x Growth',
                'services': 'Cloud Run + Cloud SQL + Memorystore',
                'changes_needed': 'Add caching layer'
            },
            {
                'phase': '100x Growth',
                'services': 'GKE + Spanner + Redis',
                'changes_needed': 'Migrate to microservices and global database'
            },
            {
                'phase': '1000x Growth',
                'services': 'Multi-region GKE + Spanner + Global LB',
                'changes_needed': 'Full global distribution'
            }
        ]
    
    def _project_scaling_costs(self, current_load: Dict[str, Any], 
                               growth_rate: float) -> Dict[str, Any]:
        """Project costs at different scales"""
        base_cost = 500  # Current monthly cost
        
        projections = {}
        for period in [3, 6, 12, 24]:
            multiplier = (1 + growth_rate) ** (period / 12)
            users = int(current_load.get('users', 1000) * multiplier)
            
            # Non-linear cost scaling
            if users < 10000:
                cost_multiplier = multiplier * 0.8  # Economies of scale
            elif users < 100000:
                cost_multiplier = multiplier * 0.6
            else:
                cost_multiplier = multiplier * 0.4
                
            projections[f'{period}_months'] = {
                'users': users,
                'monthly_cost': int(base_cost * cost_multiplier),
                'cost_per_user': round(base_cost * cost_multiplier / users, 2)
            }
        
        return projections
    
    def _create_scaling_action_plan(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create action plan for scaling"""
        return [
            {
                'priority': 1,
                'action': 'Implement caching layer',
                'timeline': 'Immediate',
                'impact': 'Reduce database load by 80%'
            },
            {
                'priority': 2,
                'action': 'Add CDN for static content',
                'timeline': 'Week 1',
                'impact': 'Reduce latency by 60%'
            },
            {
                'priority': 3,
                'action': 'Implement auto-scaling policies',
                'timeline': 'Week 2',
                'impact': 'Handle traffic spikes automatically'
            },
            {
                'priority': 4,
                'action': 'Add monitoring and alerting',
                'timeline': 'Week 3',
                'impact': 'Detect issues before users'
            }
        ]
    
    def _detect_scaling_issues(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect critical scaling issues"""
        issues = []
        
        # The killer demo - unbounded query detection
        if context.get('code_sample'):
            code = context['code_sample']
            if 'select *' in code.lower() and 'limit' not in code.lower():
                issues.append({
                    'severity': 'CRITICAL',
                    'issue': 'Unbounded query will fail at scale',
                    'current_impact': 'Works fine with 100 users',
                    'scale_impact': 'OOM crash at 10K+ users',
                    'fix': 'Add pagination: LIMIT 100 OFFSET ?',
                    'example': self._get_scaling_fix_example()
                })
        
        # Missing caching
        if not context.get('caching'):
            issues.append({
                'severity': 'HIGH',
                'issue': 'No caching strategy',
                'current_impact': 'Unnecessary database load',
                'scale_impact': 'Database overwhelmed at scale',
                'fix': 'Add Redis with 5-minute TTL',
                'example': 'Cache frequently accessed data'
            })
        
        return issues
    
    def _get_scaling_fix_example(self) -> str:
        """Get example fix for scaling issue"""
        return """
# Before (fails at scale):
@app.get("/users")
def get_users():
    return db.query("SELECT * FROM users")

# After (handles millions):
@app.get("/users")
def get_users(cursor: Optional[str] = None, limit: int = 100):
    query = "SELECT * FROM users"
    if cursor:
        query += f" WHERE id > '{cursor}'"
    query += f" ORDER BY id LIMIT {limit}"
    
    results = db.query(query)
    
    return {
        'users': results,
        'next_cursor': results[-1]['id'] if len(results) == limit else None
    }
"""
    
    def _teach_scaling_issues(self, issues: List[Dict[str, str]]):
        """Teach about scaling issues detected"""
        for issue in issues:
            if issue['severity'] == 'CRITICAL':
                self.teaching_engine.teach(
                    "🚨 SCALING DISASTER PREVENTED",
                    {
                        'what': issue['issue'],
                        'why': f"{issue['current_impact']} BUT {issue['scale_impact']}",
                        'how': issue['fix'],
                        'example': issue.get('example', '')
                    }
                )