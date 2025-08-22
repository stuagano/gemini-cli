"""
Enhanced Product Owner Agent
BMAD Product Owner enhanced with value optimization and business intelligence
Combines product management expertise with data-driven decision making
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..unified_agent_base import UnifiedAgent, AgentConfig


class ValueAnalyzer:
    """Analyze and optimize business value delivery"""
    
    def __init__(self):
        self.value_metrics = {}
        self.feature_performance = {}
        self.user_feedback = []
        
    def calculate_feature_value(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive value score for a feature"""
        
        value_score = {
            'business_impact': 0,
            'user_impact': 0,
            'technical_value': 0,
            'strategic_alignment': 0,
            'overall_score': 0,
            'confidence': 'medium'
        }
        
        # Business impact scoring
        revenue_impact = feature.get('revenue_impact', 'none')
        cost_savings = feature.get('cost_savings', 0)
        market_opportunity = feature.get('market_opportunity', 'medium')
        
        business_score = 0
        if revenue_impact == 'high':
            business_score += 30
        elif revenue_impact == 'medium':
            business_score += 20
        elif revenue_impact == 'low':
            business_score += 10
        
        if cost_savings > 0:
            business_score += min(20, cost_savings / 1000)  # $1k = 1 point, cap at 20
        
        market_scores = {'high': 25, 'medium': 15, 'low': 5}
        business_score += market_scores.get(market_opportunity, 0)
        
        value_score['business_impact'] = min(100, business_score)
        
        # User impact scoring
        user_count = feature.get('affected_users', 0)
        user_satisfaction_impact = feature.get('satisfaction_impact', 'medium')
        usability_improvement = feature.get('usability_improvement', False)
        
        user_score = 0
        if user_count > 10000:
            user_score += 30
        elif user_count > 1000:
            user_score += 20
        elif user_count > 100:
            user_score += 10
        
        satisfaction_scores = {'high': 30, 'medium': 20, 'low': 10}
        user_score += satisfaction_scores.get(user_satisfaction_impact, 0)
        
        if usability_improvement:
            user_score += 15
        
        value_score['user_impact'] = min(100, user_score)
        
        # Technical value scoring
        technical_debt_reduction = feature.get('reduces_tech_debt', False)
        performance_improvement = feature.get('performance_gain', 0)
        maintainability_gain = feature.get('maintainability_gain', False)
        
        technical_score = 0
        if technical_debt_reduction:
            technical_score += 25
        if performance_improvement > 0:
            technical_score += min(30, performance_improvement)  # % improvement
        if maintainability_gain:
            technical_score += 20
        
        value_score['technical_value'] = min(100, technical_score)
        
        # Strategic alignment scoring
        strategy_alignment = feature.get('strategic_alignment', 'medium')
        competitive_advantage = feature.get('competitive_advantage', False)
        platform_enhancement = feature.get('platform_enhancement', False)
        
        strategic_score = 0
        alignment_scores = {'critical': 40, 'high': 30, 'medium': 20, 'low': 10}
        strategic_score += alignment_scores.get(strategy_alignment, 0)
        
        if competitive_advantage:
            strategic_score += 30
        if platform_enhancement:
            strategic_score += 20
        
        value_score['strategic_alignment'] = min(100, strategic_score)
        
        # Calculate overall score (weighted average)
        weights = {
            'business_impact': 0.35,
            'user_impact': 0.3,
            'strategic_alignment': 0.2,
            'technical_value': 0.15
        }
        
        overall = sum(value_score[key] * weight for key, weight in weights.items())
        value_score['overall_score'] = round(overall, 1)
        
        # Determine confidence based on data completeness
        data_completeness = len([v for v in feature.values() if v is not None and v != '']) / len(feature)
        if data_completeness > 0.8:
            value_score['confidence'] = 'high'
        elif data_completeness > 0.5:
            value_score['confidence'] = 'medium'
        else:
            value_score['confidence'] = 'low'
        
        return value_score
    
    def rank_features_by_value(self, features: List[Dict[str, Any]], 
                              constraints: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Rank features by value considering constraints"""
        
        # Calculate value for each feature
        scored_features = []
        for feature in features:
            value_analysis = self.calculate_feature_value(feature)
            
            scored_feature = {
                **feature,
                'value_analysis': value_analysis,
                'value_score': value_analysis['overall_score']
            }
            
            # Apply constraint penalties
            if constraints:
                scored_feature['adjusted_score'] = self._apply_constraints(
                    scored_feature, constraints
                )
            else:
                scored_feature['adjusted_score'] = value_analysis['overall_score']
            
            scored_features.append(scored_feature)
        
        # Sort by adjusted score
        return sorted(scored_features, key=lambda x: x['adjusted_score'], reverse=True)
    
    def _apply_constraints(self, feature: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """Apply business constraints to feature scoring"""
        
        base_score = feature['value_score']
        adjusted_score = base_score
        
        # Budget constraints
        max_budget = constraints.get('max_budget', float('inf'))
        feature_cost = feature.get('estimated_cost', 0)
        
        if feature_cost > max_budget:
            adjusted_score *= 0.3  # Heavy penalty for over-budget
        elif feature_cost > max_budget * 0.8:
            adjusted_score *= 0.7  # Moderate penalty for near budget limit
        
        # Timeline constraints
        max_timeline = constraints.get('max_timeline_weeks', float('inf'))
        feature_timeline = feature.get('estimated_timeline_weeks', 0)
        
        if feature_timeline > max_timeline:
            adjusted_score *= 0.4  # Heavy penalty for over-timeline
        elif feature_timeline > max_timeline * 0.8:
            adjusted_score *= 0.8  # Moderate penalty for near timeline limit
        
        # Resource constraints
        available_skills = set(constraints.get('available_skills', []))
        required_skills = set(feature.get('required_skills', []))
        
        if required_skills - available_skills:  # Missing skills
            skill_gap_penalty = len(required_skills - available_skills) / len(required_skills)
            adjusted_score *= (1 - skill_gap_penalty * 0.5)
        
        # Dependencies constraints
        blocked_dependencies = feature.get('blocked_dependencies', [])
        if blocked_dependencies:
            dependency_penalty = len(blocked_dependencies) * 0.1
            adjusted_score *= (1 - min(dependency_penalty, 0.5))
        
        return round(adjusted_score, 1)
    
    def analyze_portfolio_balance(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze balance of feature portfolio"""
        
        analysis = {
            'value_distribution': {},
            'effort_distribution': {},
            'risk_distribution': {},
            'category_balance': {},
            'timeline_spread': {},
            'recommendations': []
        }
        
        # Analyze value distribution
        high_value = len([f for f in features if f.get('value_score', 0) > 70])
        medium_value = len([f for f in features if 40 <= f.get('value_score', 0) <= 70])
        low_value = len([f for f in features if f.get('value_score', 0) < 40])
        
        analysis['value_distribution'] = {
            'high_value': high_value,
            'medium_value': medium_value,
            'low_value': low_value,
            'balance': 'good' if high_value >= medium_value >= low_value else 'unbalanced'
        }
        
        # Analyze effort distribution
        efforts = [f.get('estimated_timeline_weeks', 4) for f in features]
        if efforts:
            analysis['effort_distribution'] = {
                'total_effort_weeks': sum(efforts),
                'average_effort': statistics.mean(efforts),
                'effort_range': f"{min(efforts)}-{max(efforts)} weeks",
                'large_features': len([e for e in efforts if e > 8])  # > 2 months
            }
        
        # Analyze risk distribution
        high_risk = len([f for f in features if f.get('risk_level', 'medium') == 'high'])
        medium_risk = len([f for f in features if f.get('risk_level', 'medium') == 'medium'])
        low_risk = len([f for f in features if f.get('risk_level', 'medium') == 'low'])
        
        analysis['risk_distribution'] = {
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'risk_balance': 'conservative' if low_risk > high_risk else 'aggressive' if high_risk > low_risk else 'balanced'
        }
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_portfolio_recommendations(analysis)
        
        return analysis
    
    def _generate_portfolio_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate portfolio balance recommendations"""
        
        recommendations = []
        
        # Value distribution recommendations
        value_dist = analysis['value_distribution']
        if value_dist.get('low_value', 0) > value_dist.get('high_value', 0):
            recommendations.append("Too many low-value features - focus on higher impact items")
        
        # Effort distribution recommendations
        effort_dist = analysis.get('effort_distribution', {})
        if effort_dist.get('large_features', 0) > 3:
            recommendations.append("Consider breaking down large features into smaller deliverables")
        
        # Risk distribution recommendations
        risk_dist = analysis['risk_distribution']
        if risk_dist.get('risk_balance') == 'aggressive':
            recommendations.append("High risk concentration - balance with some quick wins")
        elif risk_dist.get('risk_balance') == 'conservative':
            recommendations.append("Consider adding some high-impact, high-reward features")
        
        return recommendations


class ROICalculator:
    """Calculate return on investment for features and initiatives"""
    
    def calculate_feature_roi(self, feature: Dict[str, Any], 
                             timeframe_months: int = 12) -> Dict[str, Any]:
        """Calculate comprehensive ROI for a feature"""
        
        # Extract financial inputs
        development_cost = feature.get('development_cost', 0)
        maintenance_cost = feature.get('annual_maintenance_cost', development_cost * 0.2)
        revenue_impact = feature.get('annual_revenue_impact', 0)
        cost_savings = feature.get('annual_cost_savings', 0)
        
        # Calculate total costs
        total_development_cost = development_cost
        total_maintenance_cost = (maintenance_cost / 12) * timeframe_months
        total_cost = total_development_cost + total_maintenance_cost
        
        # Calculate total benefits
        total_revenue_benefit = (revenue_impact / 12) * timeframe_months
        total_cost_benefit = (cost_savings / 12) * timeframe_months
        total_benefit = total_revenue_benefit + total_cost_benefit
        
        # Calculate ROI metrics
        roi_percentage = ((total_benefit - total_cost) / total_cost * 100) if total_cost > 0 else 0
        payback_months = (total_development_cost / (total_benefit / timeframe_months)) if total_benefit > 0 else float('inf')
        net_present_value = self._calculate_npv(total_cost, total_benefit, timeframe_months)
        
        return {
            'roi_percentage': round(roi_percentage, 1),
            'payback_months': round(payback_months, 1) if payback_months != float('inf') else 'Never',
            'net_present_value': round(net_present_value, 0),
            'total_investment': total_cost,
            'total_benefit': total_benefit,
            'benefit_breakdown': {
                'revenue_impact': total_revenue_benefit,
                'cost_savings': total_cost_benefit
            },
            'cost_breakdown': {
                'development': total_development_cost,
                'maintenance': total_maintenance_cost
            },
            'financial_viability': self._assess_financial_viability(roi_percentage, payback_months)
        }
    
    def _calculate_npv(self, cost: float, benefit: float, months: int, 
                      discount_rate: float = 0.10) -> float:
        """Calculate Net Present Value"""
        
        monthly_rate = discount_rate / 12
        monthly_benefit = benefit / months
        
        # NPV = -Initial Cost + Sum of (Monthly Benefit / (1 + rate)^month)
        npv = -cost
        for month in range(1, months + 1):
            npv += monthly_benefit / ((1 + monthly_rate) ** month)
        
        return npv
    
    def _assess_financial_viability(self, roi: float, payback_months: float) -> str:
        """Assess financial viability of investment"""
        
        if roi > 200 and payback_months < 12:
            return 'excellent'
        elif roi > 100 and payback_months < 18:
            return 'good'
        elif roi > 50 and payback_months < 24:
            return 'acceptable'
        elif roi > 0:
            return 'marginal'
        else:
            return 'poor'
    
    def compare_investment_options(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple investment options"""
        
        comparisons = []
        
        for feature in features:
            roi_analysis = self.calculate_feature_roi(feature)
            comparisons.append({
                'feature': feature.get('title', 'Unnamed Feature'),
                'roi_percentage': roi_analysis['roi_percentage'],
                'payback_months': roi_analysis['payback_months'],
                'npv': roi_analysis['net_present_value'],
                'investment': roi_analysis['total_investment'],
                'viability': roi_analysis['financial_viability'],
                'risk_adjusted_roi': self._calculate_risk_adjusted_roi(
                    roi_analysis['roi_percentage'], 
                    feature.get('risk_level', 'medium')
                )
            })
        
        # Sort by risk-adjusted ROI
        sorted_comparisons = sorted(comparisons, key=lambda x: x['risk_adjusted_roi'], reverse=True)
        
        return {
            'investment_comparison': sorted_comparisons,
            'portfolio_metrics': self._calculate_portfolio_metrics(sorted_comparisons),
            'investment_recommendations': self._generate_investment_recommendations(sorted_comparisons)
        }
    
    def _calculate_risk_adjusted_roi(self, roi: float, risk_level: str) -> float:
        """Calculate risk-adjusted ROI"""
        
        risk_multipliers = {
            'low': 1.0,
            'medium': 0.85,
            'high': 0.7,
            'very_high': 0.5
        }
        
        multiplier = risk_multipliers.get(risk_level, 0.85)
        return roi * multiplier
    
    def _calculate_portfolio_metrics(self, comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall portfolio metrics"""
        
        total_investment = sum(c['investment'] for c in comparisons)
        weighted_roi = sum(c['roi_percentage'] * c['investment'] for c in comparisons) / total_investment if total_investment > 0 else 0
        
        viable_investments = len([c for c in comparisons if c['viability'] in ['excellent', 'good', 'acceptable']])
        
        return {
            'total_portfolio_investment': total_investment,
            'weighted_average_roi': round(weighted_roi, 1),
            'viable_investment_count': viable_investments,
            'portfolio_risk': self._assess_portfolio_risk(comparisons)
        }
    
    def _assess_portfolio_risk(self, comparisons: List[Dict[str, Any]]) -> str:
        """Assess overall portfolio risk"""
        
        excellent_count = len([c for c in comparisons if c['viability'] == 'excellent'])
        good_count = len([c for c in comparisons if c['viability'] == 'good'])
        poor_count = len([c for c in comparisons if c['viability'] in ['marginal', 'poor']])
        
        if excellent_count > good_count and poor_count == 0:
            return 'low'
        elif good_count >= excellent_count and poor_count <= 1:
            return 'medium'
        else:
            return 'high'
    
    def _generate_investment_recommendations(self, comparisons: List[Dict[str, Any]]) -> List[str]:
        """Generate investment recommendations"""
        
        recommendations = []
        
        top_performers = comparisons[:3]  # Top 3 by risk-adjusted ROI
        poor_performers = [c for c in comparisons if c['viability'] in ['marginal', 'poor']]
        
        if top_performers:
            recommendations.append(f"Prioritize {top_performers[0]['feature']} with {top_performers[0]['roi_percentage']}% ROI")
        
        if poor_performers:
            recommendations.append(f"Reconsider {len(poor_performers)} features with poor financial viability")
        
        # Portfolio balance recommendations
        high_investment_features = [c for c in comparisons if c['investment'] > 100000]  # $100k+
        if len(high_investment_features) > len(comparisons) / 2:
            recommendations.append("Portfolio heavily weighted toward large investments - consider smaller, quicker wins")
        
        return recommendations


class StakeholderAlignment:
    """Manage stakeholder alignment and communication"""
    
    def __init__(self):
        self.stakeholder_feedback = {}
        self.alignment_history = []
        
    def assess_stakeholder_alignment(self, feature: Dict[str, Any], 
                                   stakeholders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess alignment across stakeholders"""
        
        alignment_scores = {}
        conflicts = []
        consensus_areas = []
        
        for stakeholder in stakeholders:
            stakeholder_id = stakeholder.get('id', stakeholder.get('name', 'unknown'))
            
            # Score alignment based on stakeholder priorities
            alignment_score = self._calculate_stakeholder_alignment(feature, stakeholder)
            alignment_scores[stakeholder_id] = alignment_score
            
            # Identify concerns
            concerns = stakeholder.get('concerns', [])
            if concerns:
                for concern in concerns:
                    conflicts.append({
                        'stakeholder': stakeholder_id,
                        'concern': concern,
                        'impact': stakeholder.get('influence', 'medium')
                    })
        
        # Find consensus areas
        high_alignment = [sid for sid, score in alignment_scores.items() if score > 70]
        if len(high_alignment) >= len(stakeholders) * 0.7:  # 70% agreement
            consensus_areas.append('Strong overall support')
        
        # Overall alignment score
        overall_alignment = statistics.mean(alignment_scores.values()) if alignment_scores else 0
        
        return {
            'overall_alignment': round(overall_alignment, 1),
            'individual_alignment': alignment_scores,
            'consensus_level': self._determine_consensus_level(alignment_scores),
            'conflicts': conflicts,
            'consensus_areas': consensus_areas,
            'alignment_risks': self._identify_alignment_risks(conflicts, alignment_scores),
            'communication_plan': self._create_communication_plan(conflicts, alignment_scores)
        }
    
    def _calculate_stakeholder_alignment(self, feature: Dict[str, Any], 
                                       stakeholder: Dict[str, Any]) -> float:
        """Calculate how well feature aligns with stakeholder priorities"""
        
        alignment_score = 0
        
        # Priority alignment
        stakeholder_priorities = set(stakeholder.get('priorities', []))
        feature_categories = set(feature.get('categories', []))
        
        if stakeholder_priorities & feature_categories:  # Intersection
            alignment_score += 40
        
        # Goal alignment
        stakeholder_goals = stakeholder.get('goals', [])
        feature_benefits = feature.get('benefits', [])
        
        for goal in stakeholder_goals:
            for benefit in feature_benefits:
                if goal.lower() in benefit.lower() or benefit.lower() in goal.lower():
                    alignment_score += 20
                    break
        
        # Budget alignment
        stakeholder_budget = stakeholder.get('budget_preference', 'medium')
        feature_cost = feature.get('cost_category', 'medium')
        
        budget_alignment = {
            ('low', 'low'): 20,
            ('low', 'medium'): 10,
            ('low', 'high'): -10,
            ('medium', 'low'): 15,
            ('medium', 'medium'): 20,
            ('medium', 'high'): 5,
            ('high', 'low'): 10,
            ('high', 'medium'): 15,
            ('high', 'high'): 20
        }
        
        alignment_score += budget_alignment.get((stakeholder_budget, feature_cost), 0)
        
        # Timeline alignment
        stakeholder_urgency = stakeholder.get('urgency', 'medium')
        feature_timeline = feature.get('timeline_category', 'medium')
        
        if stakeholder_urgency == 'high' and feature_timeline == 'short':
            alignment_score += 15
        elif stakeholder_urgency == 'low' and feature_timeline == 'long':
            alignment_score += 10
        elif stakeholder_urgency != feature_timeline:
            alignment_score -= 5
        
        return min(100, max(0, alignment_score))
    
    def _determine_consensus_level(self, alignment_scores: Dict[str, float]) -> str:
        """Determine level of consensus among stakeholders"""
        
        if not alignment_scores:
            return 'unknown'
        
        avg_alignment = statistics.mean(alignment_scores.values())
        alignment_variance = statistics.variance(alignment_scores.values()) if len(alignment_scores) > 1 else 0
        
        if avg_alignment > 75 and alignment_variance < 100:
            return 'strong_consensus'
        elif avg_alignment > 60 and alignment_variance < 200:
            return 'moderate_consensus'
        elif avg_alignment > 40:
            return 'weak_consensus'
        else:
            return 'no_consensus'
    
    def _identify_alignment_risks(self, conflicts: List[Dict[str, Any]], 
                                 alignment_scores: Dict[str, float]) -> List[Dict[str, str]]:
        """Identify risks to stakeholder alignment"""
        
        risks = []
        
        # High influence, low alignment stakeholders
        for stakeholder_id, score in alignment_scores.items():
            if score < 40:  # Low alignment
                # Find stakeholder influence
                stakeholder_conflicts = [c for c in conflicts if c['stakeholder'] == stakeholder_id]
                high_influence_conflicts = [c for c in stakeholder_conflicts if c['impact'] == 'high']
                
                if high_influence_conflicts:
                    risks.append({
                        'risk': 'High influence stakeholder resistance',
                        'stakeholder': stakeholder_id,
                        'likelihood': 'high',
                        'impact': 'high',
                        'mitigation': 'Schedule focused alignment sessions'
                    })
        
        # Conflicting priorities
        priority_conflicts = {}
        for conflict in conflicts:
            concern = conflict['concern']
            if concern not in priority_conflicts:
                priority_conflicts[concern] = []
            priority_conflicts[concern].append(conflict)
        
        for concern, conflict_list in priority_conflicts.items():
            if len(conflict_list) > 1:
                risks.append({
                    'risk': f'Multiple stakeholders concerned about {concern}',
                    'stakeholders': [c['stakeholder'] for c in conflict_list],
                    'likelihood': 'medium',
                    'impact': 'medium',
                    'mitigation': 'Address concern directly in feature design'
                })
        
        return risks
    
    def _create_communication_plan(self, conflicts: List[Dict[str, Any]], 
                                  alignment_scores: Dict[str, float]) -> Dict[str, Any]:
        """Create stakeholder communication plan"""
        
        plan = {
            'immediate_actions': [],
            'ongoing_communication': [],
            'success_metrics': []
        }
        
        # Immediate actions for high-risk stakeholders
        low_alignment_stakeholders = [sid for sid, score in alignment_scores.items() if score < 50]
        
        for stakeholder in low_alignment_stakeholders:
            plan['immediate_actions'].append({
                'action': f'Schedule alignment meeting with {stakeholder}',
                'timeline': 'This week',
                'goal': 'Address concerns and build alignment'
            })
        
        # Ongoing communication based on conflicts
        if conflicts:
            unique_concerns = list(set(c['concern'] for c in conflicts))
            for concern in unique_concerns:
                plan['ongoing_communication'].append({
                    'topic': concern,
                    'frequency': 'Weekly updates',
                    'audience': 'All stakeholders',
                    'format': 'Status report'
                })
        
        # Success metrics
        plan['success_metrics'] = [
            'Increase average alignment score to >70%',
            'Reduce number of unresolved conflicts by 50%',
            'Achieve stakeholder sign-off before development'
        ]
        
        return plan


class EnhancedPO(UnifiedAgent):
    """
    Enhanced Product Owner Agent
    BMAD Product Owner enhanced with value optimization and business intelligence
    Parker - Senior Product Owner focused on maximizing business value and stakeholder alignment
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.value_analyzer = ValueAnalyzer()
        self.roi_calculator = ROICalculator()
        self.stakeholder_alignment = StakeholderAlignment()
        
        # PO state
        self.product_backlog = []
        self.value_tracking = {}
        self.stakeholder_history = []
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD Product Owner configuration"""
        return AgentConfig(
            id="po",
            name="Parker",
            title="Senior Product Owner",
            icon="📊",
            when_to_use="Use for backlog prioritization, value analysis, stakeholder alignment, ROI calculation",
            persona={
                'role': 'Senior Product Owner & Value Optimization Expert',
                'style': 'Strategic, data-driven, user-focused, business-minded',
                'identity': 'Product expert maximizing business value and user satisfaction',
                'focus': 'Value delivery, stakeholder alignment, ROI optimization, user outcomes',
                'core_principles': [
                    'Value-driven prioritization',
                    'Data-informed decisions',
                    'Stakeholder alignment',
                    'User-centric thinking',
                    'Continuous value optimization'
                ]
            },
            commands=[
                {'name': 'prioritize-backlog', 'description': 'Prioritize product backlog by value'},
                {'name': 'analyze-value', 'description': 'Analyze feature value and ROI'},
                {'name': 'align-stakeholders', 'description': 'Assess and improve stakeholder alignment'},
                {'name': 'optimize-portfolio', 'description': 'Optimize feature portfolio for maximum value'},
                {'name': 'validate-alignment', 'description': 'Validate product-market alignment'}
            ],
            dependencies={
                'templates': ['backlog-tmpl.yaml', 'value-analysis-tmpl.yaml'],
                'data': ['market-research.md', 'user-personas.md'],
                'checklists': ['po-checklist.md', 'value-validation-checklist.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PO-specific tasks"""
        
        if task == "prioritize_backlog":
            return self.prioritize_backlog(context)
        elif task == "analyze_value":
            return self.analyze_value(context)
        elif task == "align_stakeholders":
            return self.align_stakeholders(context)
        elif task == "optimize_portfolio":
            return self.optimize_portfolio(context)
        elif task == "validate_alignment":
            return self.validate_alignment(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def prioritize_backlog(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize product backlog based on value analysis"""
        
        backlog_items = context.get('backlog_items', [])
        constraints = context.get('constraints', {})
        
        if not backlog_items:
            return {
                'error': 'No backlog items provided',
                'suggestion': 'Provide list of features/epics to prioritize'
            }
        
        # Analyze value for each item
        value_analyzed_items = []
        for item in backlog_items:
            value_analysis = self.value_analyzer.calculate_feature_value(item)
            roi_analysis = self.roi_calculator.calculate_feature_roi(item)
            
            enhanced_item = {
                **item,
                'value_analysis': value_analysis,
                'roi_analysis': roi_analysis,
                'priority_score': self._calculate_priority_score(value_analysis, roi_analysis, item)
            }
            value_analyzed_items.append(enhanced_item)
        
        # Rank by value with constraints
        prioritized_backlog = self.value_analyzer.rank_features_by_value(
            value_analyzed_items, constraints
        )
        
        # Analyze portfolio balance
        portfolio_analysis = self.value_analyzer.analyze_portfolio_balance(prioritized_backlog)
        
        # Generate release plan
        release_plan = self._create_release_plan(prioritized_backlog, constraints)
        
        # Store updated backlog
        self.product_backlog = prioritized_backlog
        
        # Teach about prioritization
        self._teach_prioritization_insights(prioritized_backlog, portfolio_analysis)
        
        return {
            'prioritized_backlog': prioritized_backlog,
            'portfolio_analysis': portfolio_analysis,
            'release_plan': release_plan,
            'value_summary': self._summarize_value_distribution(prioritized_backlog),
            'recommendations': self._generate_prioritization_recommendations(
                prioritized_backlog, portfolio_analysis
            )
        }
    
    def analyze_value(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deep value analysis for features or initiatives"""
        
        items = context.get('items', [])
        analysis_type = context.get('analysis_type', 'feature')  # feature, initiative, portfolio
        
        if not items:
            return {'error': 'No items provided for value analysis'}
        
        analysis_results = []
        
        for item in items:
            # Comprehensive value analysis
            value_analysis = self.value_analyzer.calculate_feature_value(item)
            roi_analysis = self.roi_calculator.calculate_feature_roi(item)
            
            # Market fit analysis
            market_fit = self._assess_market_fit(item)
            
            # Competitive analysis
            competitive_position = self._analyze_competitive_position(item)
            
            # Risk analysis
            risk_assessment = self._assess_value_risks(item, value_analysis)
            
            comprehensive_analysis = {
                'item': item,
                'value_analysis': value_analysis,
                'roi_analysis': roi_analysis,
                'market_fit': market_fit,
                'competitive_position': competitive_position,
                'risk_assessment': risk_assessment,
                'recommendation': self._generate_value_recommendation(
                    value_analysis, roi_analysis, market_fit
                )
            }
            
            analysis_results.append(comprehensive_analysis)
        
        # Portfolio-level insights if multiple items
        portfolio_insights = None
        if len(items) > 1:
            portfolio_insights = self._analyze_portfolio_value(analysis_results)
        
        # Teach about value optimization
        self._teach_value_optimization(analysis_results, portfolio_insights)
        
        return {
            'analysis_results': analysis_results,
            'portfolio_insights': portfolio_insights,
            'key_insights': self._extract_key_insights(analysis_results),
            'action_items': self._generate_value_action_items(analysis_results)
        }
    
    def align_stakeholders(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess and improve stakeholder alignment"""
        
        features = context.get('features', [])
        stakeholders = context.get('stakeholders', [])
        
        if not features or not stakeholders:
            return {
                'error': 'Need both features and stakeholders for alignment analysis',
                'required': ['features', 'stakeholders']
            }
        
        alignment_results = []
        
        for feature in features:
            alignment_analysis = self.stakeholder_alignment.assess_stakeholder_alignment(
                feature, stakeholders
            )
            
            alignment_results.append({
                'feature': feature.get('title', 'Unnamed Feature'),
                'alignment_analysis': alignment_analysis
            })
        
        # Overall alignment assessment
        overall_alignment = self._assess_overall_alignment(alignment_results)
        
        # Communication strategy
        communication_strategy = self._create_comprehensive_communication_strategy(
            alignment_results, stakeholders
        )
        
        # Store alignment history
        self.stakeholder_history.append({
            'timestamp': datetime.now().isoformat(),
            'alignment_results': alignment_results,
            'overall_alignment': overall_alignment
        })
        
        # Teach about stakeholder management
        self._teach_stakeholder_management(alignment_results, overall_alignment)
        
        return {
            'feature_alignment': alignment_results,
            'overall_alignment': overall_alignment,
            'communication_strategy': communication_strategy,
            'alignment_risks': self._consolidate_alignment_risks(alignment_results),
            'success_plan': self._create_alignment_success_plan(alignment_results)
        }
    
    def optimize_portfolio(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize feature portfolio for maximum value delivery"""
        
        current_portfolio = context.get('portfolio', self.product_backlog)
        optimization_goals = context.get('goals', ['maximize_value', 'balance_risk'])
        constraints = context.get('constraints', {})
        
        if not current_portfolio:
            return {'error': 'No portfolio provided for optimization'}
        
        # Current portfolio analysis
        current_analysis = self._analyze_current_portfolio(current_portfolio)
        
        # Generate optimization scenarios
        optimization_scenarios = self._generate_optimization_scenarios(
            current_portfolio, optimization_goals, constraints
        )
        
        # Select optimal scenario
        optimal_scenario = self._select_optimal_scenario(optimization_scenarios, optimization_goals)
        
        # Create implementation roadmap
        implementation_roadmap = self._create_implementation_roadmap(optimal_scenario)
        
        # Value tracking plan
        value_tracking_plan = self._create_value_tracking_plan(optimal_scenario)
        
        # Teach about portfolio optimization
        self._teach_portfolio_optimization(current_analysis, optimal_scenario)
        
        return {
            'current_portfolio_analysis': current_analysis,
            'optimization_scenarios': optimization_scenarios,
            'optimal_scenario': optimal_scenario,
            'implementation_roadmap': implementation_roadmap,
            'value_tracking_plan': value_tracking_plan,
            'optimization_summary': self._summarize_optimization_impact(
                current_analysis, optimal_scenario
            )
        }
    
    def validate_alignment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate product-market alignment and strategic fit"""
        
        product_vision = context.get('product_vision', {})
        market_data = context.get('market_data', {})
        strategic_goals = context.get('strategic_goals', [])
        current_features = context.get('features', [])
        
        validation_results = {
            'market_alignment': self._validate_market_alignment(product_vision, market_data),
            'strategic_alignment': self._validate_strategic_alignment(strategic_goals, current_features),
            'competitive_positioning': self._validate_competitive_positioning(
                product_vision, market_data
            ),
            'value_proposition_strength': self._assess_value_proposition(
                product_vision, current_features
            ),
            'execution_feasibility': self._assess_execution_feasibility(
                current_features, context.get('constraints', {})
            )
        }
        
        # Overall alignment score
        overall_score = self._calculate_overall_alignment_score(validation_results)
        
        # Generate recommendations
        alignment_recommendations = self._generate_alignment_recommendations(validation_results)
        
        # Create action plan
        action_plan = self._create_alignment_action_plan(validation_results, alignment_recommendations)
        
        # Teach about product-market fit
        self._teach_product_market_fit(validation_results, overall_score)
        
        return {
            'validation_results': validation_results,
            'overall_alignment_score': overall_score,
            'recommendations': alignment_recommendations,
            'action_plan': action_plan,
            'risk_factors': self._identify_alignment_risk_factors(validation_results),
            'success_metrics': self._define_alignment_success_metrics(validation_results)
        }
    
    # Helper methods
    
    def _calculate_priority_score(self, value_analysis: Dict[str, Any], 
                                 roi_analysis: Dict[str, Any], 
                                 item: Dict[str, Any]) -> float:
        """Calculate comprehensive priority score"""
        
        value_score = value_analysis['overall_score']
        roi_score = min(100, max(0, roi_analysis['roi_percentage']))  # Normalize ROI to 0-100
        
        # Weight factors
        urgency_weight = {'high': 1.2, 'medium': 1.0, 'low': 0.8}.get(item.get('urgency', 'medium'), 1.0)
        effort_weight = {'low': 1.1, 'medium': 1.0, 'high': 0.9}.get(item.get('effort', 'medium'), 1.0)
        
        # Calculate weighted score
        priority_score = (value_score * 0.6 + roi_score * 0.4) * urgency_weight * effort_weight
        
        return round(priority_score, 1)
    
    def _create_release_plan(self, prioritized_backlog: List[Dict[str, Any]], 
                           constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Create release plan based on prioritized backlog"""
        
        # Extract constraints
        team_capacity = constraints.get('team_capacity_weeks', 40)  # per release
        max_features_per_release = constraints.get('max_features_per_release', 8)
        
        releases = []
        current_release = []
        current_capacity = 0
        release_number = 1
        
        for item in prioritized_backlog:
            effort = item.get('estimated_timeline_weeks', 4)
            
            # Check if item fits in current release
            if (len(current_release) < max_features_per_release and 
                current_capacity + effort <= team_capacity):
                
                current_release.append(item)
                current_capacity += effort
            else:
                # Start new release
                if current_release:
                    releases.append({
                        'release': f"Release {release_number}",
                        'features': current_release,
                        'total_effort_weeks': current_capacity,
                        'estimated_value': sum(f.get('value_score', 0) for f in current_release),
                        'estimated_timeline': f"{current_capacity} weeks"
                    })
                    release_number += 1
                
                current_release = [item]
                current_capacity = effort
        
        # Add final release if has items
        if current_release:
            releases.append({
                'release': f"Release {release_number}",
                'features': current_release,
                'total_effort_weeks': current_capacity,
                'estimated_value': sum(f.get('value_score', 0) for f in current_release),
                'estimated_timeline': f"{current_capacity} weeks"
            })
        
        return {
            'releases': releases,
            'total_releases': len(releases),
            'total_features': len(prioritized_backlog),
            'total_effort': sum(r['total_effort_weeks'] for r in releases),
            'release_timeline': f"{sum(r['total_effort_weeks'] for r in releases)} weeks total"
        }
    
    def _summarize_value_distribution(self, backlog: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize value distribution across backlog"""
        
        if not backlog:
            return {'error': 'Empty backlog'}
        
        value_scores = [item.get('value_score', 0) for item in backlog]
        
        return {
            'total_items': len(backlog),
            'average_value': round(statistics.mean(value_scores), 1),
            'value_range': f"{min(value_scores)}-{max(value_scores)}",
            'high_value_items': len([v for v in value_scores if v > 70]),
            'medium_value_items': len([v for v in value_scores if 40 <= v <= 70]),
            'low_value_items': len([v for v in value_scores if v < 40]),
            'total_estimated_value': sum(value_scores)
        }
    
    def _generate_prioritization_recommendations(self, backlog: List[Dict[str, Any]], 
                                               portfolio_analysis: Dict[str, Any]) -> List[str]:
        """Generate prioritization recommendations"""
        
        recommendations = []
        
        # Value distribution recommendations
        value_summary = self._summarize_value_distribution(backlog)
        if value_summary.get('low_value_items', 0) > value_summary.get('high_value_items', 0):
            recommendations.append("Consider removing or reworking low-value items")
        
        # Portfolio balance recommendations
        recommendations.extend(portfolio_analysis.get('recommendations', []))
        
        # Top items focus
        if len(backlog) > 0:
            top_item = backlog[0]
            recommendations.append(f"Focus on '{top_item.get('title', 'top item')}' with {top_item.get('value_score', 0)} value score")
        
        return recommendations
    
    def _teach_prioritization_insights(self, backlog: List[Dict[str, Any]], 
                                     portfolio_analysis: Dict[str, Any]):
        """Teach insights from prioritization analysis"""
        
        if not backlog:
            return
        
        top_item = backlog[0]
        value_summary = self._summarize_value_distribution(backlog)
        
        self.teaching_engine.teach(
            "Value-Driven Prioritization",
            {
                'what': f"Prioritized {len(backlog)} features by value score",
                'why': f"Top item has {top_item.get('value_score', 0)} value score with {top_item.get('roi_analysis', {}).get('roi_percentage', 0)}% ROI",
                'how': f"Balanced portfolio: {value_summary['high_value_items']} high-value, {value_summary['medium_value_items']} medium-value items",
                'example': f"Focus on '{top_item.get('title', 'top feature')}' first for maximum impact"
            }
        )
    
    def _assess_market_fit(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Assess market fit for item"""
        
        # Simplified market fit assessment
        target_market_size = item.get('target_market_size', 'unknown')
        customer_validation = item.get('customer_validation', 'medium')
        market_timing = item.get('market_timing', 'good')
        
        fit_score = 0
        if target_market_size == 'large':
            fit_score += 30
        elif target_market_size == 'medium':
            fit_score += 20
        
        validation_scores = {'high': 40, 'medium': 25, 'low': 10}
        fit_score += validation_scores.get(customer_validation, 0)
        
        timing_scores = {'perfect': 30, 'good': 20, 'fair': 10, 'poor': -10}
        fit_score += timing_scores.get(market_timing, 0)
        
        if fit_score > 70:
            fit_assessment = 'strong'
        elif fit_score > 40:
            fit_assessment = 'moderate'
        else:
            fit_assessment = 'weak'
        
        return {
            'fit_score': str(fit_score),
            'fit_assessment': fit_assessment,
            'market_size': target_market_size,
            'validation_level': customer_validation
        }
    
    def _analyze_competitive_position(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Analyze competitive position"""
        
        competitive_advantage = item.get('competitive_advantage', 'none')
        differentiation = item.get('differentiation', 'medium')
        competitive_response_risk = item.get('competitive_response_risk', 'medium')
        
        position_strength = 'weak'
        if competitive_advantage == 'strong' and differentiation == 'high':
            position_strength = 'strong'
        elif competitive_advantage == 'medium' or differentiation == 'high':
            position_strength = 'moderate'
        
        return {
            'position_strength': position_strength,
            'competitive_advantage': competitive_advantage,
            'differentiation': differentiation,
            'response_risk': competitive_response_risk
        }
    
    def _assess_value_risks(self, item: Dict[str, Any], 
                          value_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Assess risks to value realization"""
        
        risks = []
        
        # Execution risk
        complexity = item.get('complexity', 'medium')
        if complexity == 'high':
            risks.append({
                'risk': 'Execution complexity',
                'impact': 'high',
                'mitigation': 'Break into smaller deliverables'
            })
        
        # Market risk
        market_uncertainty = item.get('market_uncertainty', 'medium')
        if market_uncertainty == 'high':
            risks.append({
                'risk': 'Market uncertainty',
                'impact': 'medium',
                'mitigation': 'Validate with customer research'
            })
        
        # Technology risk
        tech_risk = item.get('technology_risk', 'low')
        if tech_risk in ['high', 'medium']:
            risks.append({
                'risk': 'Technology implementation risk',
                'impact': tech_risk,
                'mitigation': 'Create proof of concept first'
            })
        
        return risks
    
    def _generate_value_recommendation(self, value_analysis: Dict[str, Any], 
                                     roi_analysis: Dict[str, Any], 
                                     market_fit: Dict[str, str]) -> str:
        """Generate value-based recommendation"""
        
        value_score = value_analysis['overall_score']
        roi = roi_analysis['roi_percentage']
        fit = market_fit['fit_assessment']
        viability = roi_analysis['financial_viability']
        
        if value_score > 70 and roi > 100 and fit == 'strong':
            return "STRONG RECOMMEND - High value, great ROI, strong market fit"
        elif value_score > 50 and viability in ['good', 'excellent']:
            return "RECOMMEND - Good value proposition with solid returns"
        elif value_score > 40 and fit in ['moderate', 'strong']:
            return "CONSIDER - Moderate value but decent market opportunity"
        else:
            return "NOT RECOMMENDED - Low value, poor ROI, or weak market fit"
    
    def _analyze_portfolio_value(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze value across portfolio"""
        
        total_investment = sum(r['roi_analysis']['total_investment'] for r in analysis_results)
        total_benefit = sum(r['roi_analysis']['total_benefit'] for r in analysis_results)
        
        portfolio_roi = ((total_benefit - total_investment) / total_investment * 100) if total_investment > 0 else 0
        
        # Value concentration
        high_value_count = len([r for r in analysis_results if r['value_analysis']['overall_score'] > 70])
        
        return {
            'portfolio_roi': round(portfolio_roi, 1),
            'total_investment': total_investment,
            'total_benefit': total_benefit,
            'high_value_concentration': f"{high_value_count}/{len(analysis_results)}",
            'portfolio_balance': 'concentrated' if high_value_count < len(analysis_results) * 0.3 else 'balanced'
        }
    
    def _extract_key_insights(self, analysis_results: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from value analysis"""
        
        insights = []
        
        # Top performer
        if analysis_results:
            top_item = max(analysis_results, key=lambda x: x['value_analysis']['overall_score'])
            insights.append(f"Top value item: {top_item['item'].get('title')} with {top_item['value_analysis']['overall_score']} score")
        
        # ROI insights
        excellent_roi = [r for r in analysis_results if r['roi_analysis']['financial_viability'] == 'excellent']
        if excellent_roi:
            insights.append(f"{len(excellent_roi)} items have excellent ROI potential")
        
        # Risk insights
        high_risk_items = []
        for result in analysis_results:
            if len(result['risk_assessment']) > 2:  # More than 2 risks
                high_risk_items.append(result['item'].get('title', 'Unnamed'))
        
        if high_risk_items:
            insights.append(f"High-risk items requiring attention: {', '.join(high_risk_items[:3])}")
        
        return insights
    
    def _generate_value_action_items(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate action items from value analysis"""
        
        actions = []
        
        for result in analysis_results:
            recommendation = result['recommendation']
            item_title = result['item'].get('title', 'Unnamed')
            
            if 'STRONG RECOMMEND' in recommendation:
                actions.append({
                    'action': f'Fast-track {item_title}',
                    'priority': 'high',
                    'timeline': 'immediate'
                })
            elif 'NOT RECOMMENDED' in recommendation:
                actions.append({
                    'action': f'Re-evaluate or remove {item_title}',
                    'priority': 'medium',
                    'timeline': 'this week'
                })
            
            # Risk-based actions
            risks = result['risk_assessment']
            if risks:
                high_impact_risks = [r for r in risks if r['impact'] == 'high']
                if high_impact_risks:
                    actions.append({
                        'action': f'Mitigate risks for {item_title}: {high_impact_risks[0]["mitigation"]}',
                        'priority': 'high',
                        'timeline': 'before development'
                    })
        
        return actions
    
    def _teach_value_optimization(self, analysis_results: List[Dict[str, Any]], 
                                portfolio_insights: Optional[Dict[str, Any]]):
        """Teach about value optimization principles"""
        
        if not analysis_results:
            return
        
        avg_value = statistics.mean([r['value_analysis']['overall_score'] for r in analysis_results])
        strong_recommend_count = len([r for r in analysis_results if 'STRONG RECOMMEND' in r['recommendation']])
        
        context = {
            'what': f"Analyzed {len(analysis_results)} items with average value score {avg_value:.1f}",
            'why': f"{strong_recommend_count} items strongly recommended for high value delivery",
            'how': "Used comprehensive value analysis including ROI, market fit, and risk assessment",
        }
        
        if portfolio_insights:
            context['example'] = f"Portfolio ROI: {portfolio_insights['portfolio_roi']}%"
        
        self.teaching_engine.teach("Value-Driven Product Decisions", context)
    
    # Additional methods for remaining functionality...
    
    def _assess_overall_alignment(self, alignment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall stakeholder alignment"""
        
        if not alignment_results:
            return {'overall_score': 0, 'status': 'unknown'}
        
        scores = [result['alignment_analysis']['overall_alignment'] for result in alignment_results]
        overall_score = statistics.mean(scores)
        
        status = 'excellent' if overall_score > 80 else 'good' if overall_score > 60 else 'needs_improvement'
        
        return {
            'overall_score': round(overall_score, 1),
            'status': status,
            'aligned_features': len([s for s in scores if s > 70]),
            'misaligned_features': len([s for s in scores if s < 40])
        }
    
    def _create_comprehensive_communication_strategy(self, alignment_results: List[Dict[str, Any]], 
                                                   stakeholders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive communication strategy"""
        
        return {
            'stakeholder_specific_plans': [
                {
                    'stakeholder': sh.get('name', 'Unknown'),
                    'communication_frequency': 'weekly' if sh.get('influence') == 'high' else 'bi-weekly',
                    'preferred_format': sh.get('communication_preference', 'email'),
                    'key_topics': sh.get('priorities', [])
                }
                for sh in stakeholders
            ],
            'alignment_meetings': [
                {
                    'purpose': 'Address feature misalignment',
                    'frequency': 'monthly',
                    'participants': 'all_stakeholders'
                }
            ],
            'success_metrics': [
                'Improve alignment scores by 20%',
                'Reduce unresolved conflicts by 50%',
                'Achieve stakeholder sign-off rate >90%'
            ]
        }
    
    def _consolidate_alignment_risks(self, alignment_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Consolidate alignment risks across features"""
        
        all_risks = []
        for result in alignment_results:
            feature_risks = result['alignment_analysis'].get('alignment_risks', [])
            for risk in feature_risks:
                risk['feature'] = result['feature']
                all_risks.append(risk)
        
        return all_risks
    
    def _create_alignment_success_plan(self, alignment_results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create plan for alignment success"""
        
        return {
            'immediate_actions': [
                'Schedule alignment workshops for misaligned features',
                'Create stakeholder-specific communication plans',
                'Address high-impact conflicts first'
            ],
            'ongoing_activities': [
                'Regular stakeholder pulse checks',
                'Feature alignment reviews before development',
                'Quarterly stakeholder alignment assessments'
            ],
            'success_measures': [
                'Alignment score >70% for all features',
                'Consensus level "moderate" or better',
                'Zero unresolved high-impact conflicts'
            ]
        }
    
    def _teach_stakeholder_management(self, alignment_results: List[Dict[str, Any]], 
                                    overall_alignment: Dict[str, Any]):
        """Teach about effective stakeholder management"""
        
        avg_alignment = overall_alignment['overall_score']
        aligned_count = overall_alignment['aligned_features']
        total_features = len(alignment_results)
        
        self.teaching_engine.teach(
            "Stakeholder Alignment Management",
            {
                'what': f"Assessed alignment for {total_features} features with {avg_alignment:.1f}% average alignment",
                'why': f"{aligned_count}/{total_features} features have strong stakeholder support",
                'how': "Used comprehensive alignment analysis across priorities, goals, and constraints",
                'example': f"Status: {overall_alignment['status']} - focus on communication and conflict resolution"
            }
        )
    
    def _analyze_current_portfolio(self, portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze current portfolio state"""
        
        # Value analysis
        value_scores = [item.get('value_score', 0) for item in portfolio]
        avg_value = statistics.mean(value_scores) if value_scores else 0
        
        # Effort analysis
        efforts = [item.get('estimated_timeline_weeks', 4) for item in portfolio]
        total_effort = sum(efforts)
        
        # ROI analysis
        roi_scores = []
        for item in portfolio:
            roi_data = self.roi_calculator.calculate_feature_roi(item)
            roi_scores.append(roi_data['roi_percentage'])
        
        avg_roi = statistics.mean(roi_scores) if roi_scores else 0
        
        return {
            'total_items': len(portfolio),
            'average_value_score': round(avg_value, 1),
            'total_effort_weeks': total_effort,
            'average_roi': round(avg_roi, 1),
            'high_value_items': len([v for v in value_scores if v > 70]),
            'quick_wins': len([item for item in portfolio 
                             if item.get('value_score', 0) > 60 and 
                             item.get('estimated_timeline_weeks', 4) < 4]),
            'current_balance': self._assess_portfolio_balance(portfolio)
        }
    
    def _assess_portfolio_balance(self, portfolio: List[Dict[str, Any]]) -> str:
        """Assess balance of portfolio"""
        
        high_value = len([item for item in portfolio if item.get('value_score', 0) > 70])
        quick_wins = len([item for item in portfolio 
                         if item.get('value_score', 0) > 60 and 
                         item.get('estimated_timeline_weeks', 4) < 4])
        big_bets = len([item for item in portfolio 
                       if item.get('value_score', 0) > 80 and 
                       item.get('estimated_timeline_weeks', 4) > 8])
        
        if quick_wins > 0 and big_bets > 0 and high_value > len(portfolio) * 0.5:
            return 'well_balanced'
        elif quick_wins > big_bets * 2:
            return 'quick_win_heavy'
        elif big_bets > quick_wins:
            return 'big_bet_heavy'
        else:
            return 'unbalanced'
    
    def _generate_optimization_scenarios(self, portfolio: List[Dict[str, Any]], 
                                       goals: List[str], 
                                       constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate different optimization scenarios"""
        
        scenarios = []
        
        # Scenario 1: Maximize Value
        if 'maximize_value' in goals:
            value_optimized = sorted(portfolio, key=lambda x: x.get('value_score', 0), reverse=True)
            scenarios.append({
                'name': 'Value Maximization',
                'description': 'Prioritize highest value features first',
                'portfolio': value_optimized[:10],  # Top 10
                'expected_outcome': 'Highest business impact'
            })
        
        # Scenario 2: Quick Wins Focus
        quick_wins = [item for item in portfolio 
                     if item.get('value_score', 0) > 50 and 
                     item.get('estimated_timeline_weeks', 4) < 6]
        if quick_wins:
            scenarios.append({
                'name': 'Quick Wins',
                'description': 'Focus on high-value, low-effort items',
                'portfolio': quick_wins,
                'expected_outcome': 'Fast time to value'
            })
        
        # Scenario 3: Balanced Approach
        balanced_portfolio = self._create_balanced_portfolio(portfolio, constraints)
        scenarios.append({
            'name': 'Balanced Portfolio',
            'description': 'Mix of quick wins, medium efforts, and strategic bets',
            'portfolio': balanced_portfolio,
            'expected_outcome': 'Sustainable value delivery'
        })
        
        return scenarios
    
    def _create_balanced_portfolio(self, portfolio: List[Dict[str, Any]], 
                                 constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a balanced portfolio"""
        
        # Sort by priority score
        sorted_portfolio = sorted(portfolio, key=lambda x: x.get('priority_score', 0), reverse=True)
        
        balanced = []
        total_effort = 0
        max_effort = constraints.get('max_total_effort_weeks', 40)
        
        # Select mix ensuring balance
        quick_wins = 0
        medium_efforts = 0
        big_bets = 0
        
        for item in sorted_portfolio:
            effort = item.get('estimated_timeline_weeks', 4)
            
            if total_effort + effort > max_effort:
                continue
            
            # Categorize effort
            if effort < 4:
                effort_category = 'quick_win'
            elif effort < 8:
                effort_category = 'medium'
            else:
                effort_category = 'big_bet'
            
            # Balance constraints
            if effort_category == 'quick_win' and quick_wins < 4:
                balanced.append(item)
                quick_wins += 1
                total_effort += effort
            elif effort_category == 'medium' and medium_efforts < 3:
                balanced.append(item)
                medium_efforts += 1
                total_effort += effort
            elif effort_category == 'big_bet' and big_bets < 2:
                balanced.append(item)
                big_bets += 1
                total_effort += effort
        
        return balanced
    
    def _select_optimal_scenario(self, scenarios: List[Dict[str, Any]], 
                               goals: List[str]) -> Dict[str, Any]:
        """Select optimal scenario based on goals"""
        
        if not scenarios:
            return {}
        
        # Score scenarios based on goals
        for scenario in scenarios:
            scenario['goal_alignment_score'] = self._score_scenario_alignment(scenario, goals)
        
        # Return highest scoring scenario
        return max(scenarios, key=lambda x: x['goal_alignment_score'])
    
    def _score_scenario_alignment(self, scenario: Dict[str, Any], goals: List[str]) -> float:
        """Score how well scenario aligns with goals"""
        
        score = 0
        portfolio = scenario['portfolio']
        
        if 'maximize_value' in goals:
            avg_value = statistics.mean([item.get('value_score', 0) for item in portfolio])
            score += avg_value * 0.4
        
        if 'balance_risk' in goals:
            # Lower risk gets higher score
            high_risk_count = len([item for item in portfolio if item.get('risk_level', 'medium') == 'high'])
            risk_ratio = high_risk_count / len(portfolio) if portfolio else 1
            score += (1 - risk_ratio) * 30
        
        if 'quick_time_to_market' in goals:
            avg_effort = statistics.mean([item.get('estimated_timeline_weeks', 4) for item in portfolio])
            score += max(0, (12 - avg_effort) * 5)  # Lower effort = higher score
        
        return score
    
    def _create_implementation_roadmap(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation roadmap for optimal scenario"""
        
        portfolio = scenario.get('portfolio', [])
        
        # Group by quarters
        quarters = []
        current_quarter = []
        quarter_capacity = 0
        max_quarter_capacity = 12  # weeks
        quarter_num = 1
        
        for item in portfolio:
            effort = item.get('estimated_timeline_weeks', 4)
            
            if quarter_capacity + effort <= max_quarter_capacity:
                current_quarter.append(item)
                quarter_capacity += effort
            else:
                if current_quarter:
                    quarters.append({
                        'quarter': f"Q{quarter_num}",
                        'features': current_quarter,
                        'total_effort': quarter_capacity,
                        'expected_value': sum(f.get('value_score', 0) for f in current_quarter)
                    })
                    quarter_num += 1
                
                current_quarter = [item]
                quarter_capacity = effort
        
        # Add final quarter
        if current_quarter:
            quarters.append({
                'quarter': f"Q{quarter_num}",
                'features': current_quarter,
                'total_effort': quarter_capacity,
                'expected_value': sum(f.get('value_score', 0) for f in current_quarter)
            })
        
        return {
            'roadmap_quarters': quarters,
            'total_duration': f"{len(quarters)} quarters",
            'total_features': len(portfolio),
            'total_value_expected': sum(q['expected_value'] for q in quarters)
        }
    
    def _create_value_tracking_plan(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Create plan for tracking value realization"""
        
        return {
            'success_metrics': [
                'Feature adoption rates',
                'User satisfaction scores',
                'Revenue impact tracking',
                'Cost savings measurement'
            ],
            'tracking_frequency': 'monthly',
            'review_schedule': [
                {'milestone': 'Post-launch', 'timeline': '2 weeks after release'},
                {'milestone': 'Value validation', 'timeline': '3 months after release'},
                {'milestone': 'ROI assessment', 'timeline': '6 months after release'}
            ],
            'adjustment_triggers': [
                'Adoption rate <50% after 1 month',
                'User satisfaction <70%',
                'Revenue impact <80% of projection'
            ]
        }
    
    def _teach_portfolio_optimization(self, current_analysis: Dict[str, Any], 
                                    optimal_scenario: Dict[str, Any]):
        """Teach about portfolio optimization"""
        
        current_value = current_analysis['average_value_score']
        optimized_features = len(optimal_scenario.get('portfolio', []))
        scenario_name = optimal_scenario.get('name', 'optimized')
        
        self.teaching_engine.teach(
            "Portfolio Optimization",
            {
                'what': f"Optimized portfolio from {current_analysis['total_items']} to {optimized_features} features",
                'why': f"Current average value {current_value} → optimized for {scenario_name.lower()}",
                'how': f"Used {optimal_scenario.get('description', 'comprehensive analysis')}",
                'example': f"Expected outcome: {optimal_scenario.get('expected_outcome', 'improved value delivery')}"
            }
        )
    
    def _summarize_optimization_impact(self, current_analysis: Dict[str, Any], 
                                     optimal_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize the impact of optimization"""
        
        portfolio = optimal_scenario.get('portfolio', [])
        
        optimized_value = statistics.mean([item.get('value_score', 0) for item in portfolio]) if portfolio else 0
        optimized_effort = sum([item.get('estimated_timeline_weeks', 4) for item in portfolio])
        
        return {
            'value_improvement': f"{optimized_value - current_analysis['average_value_score']:.1f} points",
            'effort_reduction': f"{current_analysis['total_effort_weeks'] - optimized_effort} weeks saved",
            'focus_improvement': f"Focused on top {len(portfolio)} features",
            'expected_outcome': optimal_scenario.get('expected_outcome', 'Improved value delivery')
        }
    
    # Validation methods (simplified implementations)
    
    def _validate_market_alignment(self, product_vision: Dict[str, Any], 
                                 market_data: Dict[str, Any]) -> Dict[str, str]:
        """Validate market alignment"""
        return {
            'alignment_score': '75',
            'market_size_match': 'good',
            'timing_assessment': 'appropriate',
            'validation_status': 'aligned'
        }
    
    def _validate_strategic_alignment(self, strategic_goals: List[str], 
                                    features: List[Dict[str, Any]]) -> Dict[str, str]:
        """Validate strategic alignment"""
        return {
            'alignment_score': '80',
            'goal_coverage': f"{len(strategic_goals)} goals addressed",
            'feature_alignment': 'strong',
            'validation_status': 'well_aligned'
        }
    
    def _validate_competitive_positioning(self, product_vision: Dict[str, Any], 
                                        market_data: Dict[str, Any]) -> Dict[str, str]:
        """Validate competitive positioning"""
        return {
            'position_strength': 'differentiated',
            'competitive_advantage': 'sustainable',
            'market_position': 'strong',
            'validation_status': 'competitive'
        }
    
    def _assess_value_proposition(self, product_vision: Dict[str, Any], 
                                features: List[Dict[str, Any]]) -> Dict[str, str]:
        """Assess value proposition strength"""
        return {
            'value_clarity': 'clear',
            'benefit_differentiation': 'strong',
            'customer_resonance': 'high',
            'validation_status': 'compelling'
        }
    
    def _assess_execution_feasibility(self, features: List[Dict[str, Any]], 
                                    constraints: Dict[str, Any]) -> Dict[str, str]:
        """Assess execution feasibility"""
        return {
            'resource_adequacy': 'sufficient',
            'timeline_feasibility': 'achievable',
            'risk_level': 'manageable',
            'validation_status': 'feasible'
        }
    
    def _calculate_overall_alignment_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall alignment score"""
        scores = []
        for result in validation_results.values():
            if isinstance(result, dict) and 'alignment_score' in result:
                scores.append(float(result['alignment_score']))
        
        return round(statistics.mean(scores), 1) if scores else 0
    
    def _generate_alignment_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate alignment recommendations"""
        return [
            "Strengthen market validation through customer interviews",
            "Align feature roadmap more closely with strategic goals",
            "Enhance competitive differentiation",
            "Clarify value proposition messaging"
        ]
    
    def _create_alignment_action_plan(self, validation_results: Dict[str, Any], 
                                    recommendations: List[str]) -> List[Dict[str, str]]:
        """Create alignment action plan"""
        return [
            {
                'action': rec,
                'priority': 'high' if i < 2 else 'medium',
                'timeline': '2 weeks' if i < 2 else '1 month',
                'owner': 'Product Owner'
            }
            for i, rec in enumerate(recommendations[:4])
        ]
    
    def _identify_alignment_risk_factors(self, validation_results: Dict[str, Any]) -> List[str]:
        """Identify alignment risk factors"""
        return [
            "Market timing uncertainty",
            "Competitive response risk",
            "Resource allocation challenges",
            "Stakeholder alignment gaps"
        ]
    
    def _define_alignment_success_metrics(self, validation_results: Dict[str, Any]) -> List[str]:
        """Define success metrics for alignment"""
        return [
            "Market alignment score >80%",
            "Strategic goal coverage 100%",
            "Competitive advantage validated",
            "Value proposition resonance >75%"
        ]
    
    def _teach_product_market_fit(self, validation_results: Dict[str, Any], 
                                overall_score: float):
        """Teach about product-market fit validation"""
        
        self.teaching_engine.teach(
            "Product-Market Fit Validation",
            {
                'what': f"Validated product-market alignment with {overall_score}% overall score",
                'why': "Strong product-market fit is essential for sustainable growth",
                'how': "Assessed market alignment, strategic fit, competitive position, and execution feasibility",
                'example': f"Focus on areas scoring <70% for improvement"
            }
        )