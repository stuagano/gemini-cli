"""
Knowledge Integration Module for Gemini Enterprise Architect Agents
Provides seamless integration between agents and the knowledge system
"""

from typing import List, Dict, Any, Optional, Callable, Union
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
import json
from abc import ABC, abstractmethod

from .rag_system import EnterpriseRAGSystem, RAGQuery, RAGResponse
from .knowledge_base import EnterpriseKnowledgeBase
from .vector_store import EnterpriseVectorStore

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeContext:
    """Context for knowledge queries from agents"""
    agent_id: str
    agent_type: str
    session_id: str
    user_context: Dict[str, Any] = field(default_factory=dict)
    project_context: Dict[str, Any] = field(default_factory=dict)
    previous_queries: List[str] = field(default_factory=list)

@dataclass
class EnhancedAgentResponse:
    """Agent response enhanced with knowledge system insights"""
    original_response: str
    knowledge_enhanced_response: str
    supporting_evidence: List[Dict[str, Any]]
    confidence_boost: float
    suggested_actions: List[str]
    related_documentation: List[str]

class KnowledgeIntegrationMixin:
    """Mixin class to add knowledge capabilities to any agent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_provider: Optional['AgentKnowledgeProvider'] = None
        self.knowledge_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
    def set_knowledge_provider(self, provider: 'AgentKnowledgeProvider') -> None:
        """Set the knowledge provider for this agent"""
        self.knowledge_provider = provider
        logger.info(f"Knowledge provider set for agent {getattr(self, 'name', 'Unknown')}")
    
    async def query_knowledge(self, query: str, query_type: str = "general",
                            context: Dict[str, Any] = None) -> RAGResponse:
        """Query the knowledge system with agent context"""
        if not self.knowledge_provider:
            logger.warning("No knowledge provider available")
            return self._create_empty_response(query)
        
        # Create knowledge context
        knowledge_context = KnowledgeContext(
            agent_id=getattr(self, 'agent_id', 'unknown'),
            agent_type=getattr(self, 'agent_type', 'generic'),
            session_id=getattr(self, 'session_id', 'default'),
            user_context=context or {},
            project_context=getattr(self, 'project_context', {}),
            previous_queries=getattr(self, 'query_history', [])
        )
        
        return await self.knowledge_provider.query_with_context(
            query, query_type, knowledge_context
        )
    
    async def enhance_response(self, response: str, context: Dict[str, Any] = None) -> EnhancedAgentResponse:
        """Enhance agent response with knowledge system insights"""
        if not self.knowledge_provider:
            return EnhancedAgentResponse(
                original_response=response,
                knowledge_enhanced_response=response,
                supporting_evidence=[],
                confidence_boost=0.0,
                suggested_actions=[],
                related_documentation=[]
            )
        
        return await self.knowledge_provider.enhance_agent_response(
            response, getattr(self, 'agent_type', 'generic'), context
        )
    
    async def get_recommendations(self, requirements: str, 
                                context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get service recommendations from knowledge system"""
        if not self.knowledge_provider:
            return []
        
        return await self.knowledge_provider.get_service_recommendations(
            requirements, getattr(self, 'agent_type', 'generic'), context
        )
    
    async def validate_against_best_practices(self, proposal: str,
                                           domain: str = "general") -> Dict[str, Any]:
        """Validate a proposal against GCP best practices"""
        if not self.knowledge_provider:
            return {'validation_available': False}
        
        return await self.knowledge_provider.validate_best_practices(
            proposal, domain, getattr(self, 'agent_type', 'generic')
        )
    
    def _create_empty_response(self, query: str) -> RAGResponse:
        """Create an empty response when knowledge provider is unavailable"""
        return RAGResponse(
            answer="Knowledge system not available for this query.",
            sources=[],
            confidence=0.0,
            query_id=f"empty_{hash(query)}",
            response_time_ms=0,
            reasoning="No knowledge provider available"
        )

class AgentKnowledgeProvider:
    """Provides knowledge services specifically tailored for agents"""
    
    def __init__(self, rag_system: EnterpriseRAGSystem):
        self.rag_system = rag_system
        self.agent_contexts: Dict[str, KnowledgeContext] = {}
        self.response_cache: Dict[str, Any] = {}
        
        # Agent-specific query templates
        self.agent_query_templates = {
            'architect': {
                'system_design': "Design a scalable GCP architecture for: {query}",
                'service_selection': "Which GCP services are best for: {query}",
                'best_practices': "What are the GCP best practices for: {query}"
            },
            'developer': {
                'implementation': "How do I implement: {query}",
                'code_example': "Provide a code example for: {query}",
                'troubleshooting': "How do I troubleshoot: {query}"
            },
            'qa': {
                'testing_strategy': "How should I test: {query}",
                'quality_validation': "How do I validate quality for: {query}",
                'regression_prevention': "How do I prevent regressions in: {query}"
            },
            'scout': {
                'codebase_analysis': "How do I analyze: {query}",
                'dependency_mapping': "Map dependencies for: {query}",
                'technical_debt': "Identify technical debt in: {query}"
            },
            'po': {
                'value_analysis': "What is the business value of: {query}",
                'stakeholder_impact': "How does this impact stakeholders: {query}",
                'roi_calculation': "Calculate ROI for: {query}"
            }
        }
    
    async def query_with_context(self, query: str, query_type: str,
                               knowledge_context: KnowledgeContext) -> RAGResponse:
        """Query knowledge system with full agent context"""
        # Enhance query based on agent type
        enhanced_query = self._enhance_query_for_agent(query, knowledge_context.agent_type, query_type)
        
        # Create RAG query with context
        rag_query = RAGQuery(
            query=enhanced_query,
            context={
                'agent_id': knowledge_context.agent_id,
                'agent_type': knowledge_context.agent_type,
                'session_id': knowledge_context.session_id,
                **knowledge_context.user_context,
                **knowledge_context.project_context
            },
            user_id=knowledge_context.session_id,
            session_id=knowledge_context.session_id,
            query_type=query_type,
            max_context_chunks=self._get_context_chunks_for_agent(knowledge_context.agent_type)
        )
        
        # Execute query
        response = await self.rag_system.query(rag_query)
        
        # Store context for future queries
        self.agent_contexts[knowledge_context.agent_id] = knowledge_context
        
        # Add to query history
        if knowledge_context.agent_id in self.agent_contexts:
            self.agent_contexts[knowledge_context.agent_id].previous_queries.append(query)
        
        return response
    
    async def enhance_agent_response(self, response: str, agent_type: str,
                                   context: Dict[str, Any] = None) -> EnhancedAgentResponse:
        """Enhance an agent's response with knowledge system insights"""
        # Extract key concepts from response
        key_concepts = self._extract_key_concepts(response)
        
        # Query for supporting evidence
        supporting_evidence = []
        for concept in key_concepts[:3]:  # Limit to top 3 concepts
            try:
                evidence_query = RAGQuery(
                    query=f"Best practices and documentation for {concept}",
                    query_type="general",
                    context={'agent_type': agent_type, **(context or {})},
                    max_context_chunks=2
                )
                evidence_response = await self.rag_system.query(evidence_query)
                
                if evidence_response.sources:
                    for source in evidence_response.sources[:1]:  # One source per concept
                        supporting_evidence.append({
                            'concept': concept,
                            'title': source.title,
                            'url': source.url,
                            'snippet': source.content[:200] + '...' if len(source.content) > 200 else source.content,
                            'confidence': getattr(source, 'confidence_score', 0.8)
                        })
            except Exception as e:
                logger.warning(f"Could not get evidence for concept {concept}: {e}")
        
        # Generate suggested actions based on agent type
        suggested_actions = self._generate_agent_actions(response, agent_type)
        
        # Find related documentation
        related_docs = [evidence['url'] for evidence in supporting_evidence if evidence['url']]
        
        # Calculate confidence boost
        confidence_boost = min(0.3, len(supporting_evidence) * 0.1)
        
        # Enhance the response text
        enhanced_response = self._enhance_response_text(response, supporting_evidence)
        
        return EnhancedAgentResponse(
            original_response=response,
            knowledge_enhanced_response=enhanced_response,
            supporting_evidence=supporting_evidence,
            confidence_boost=confidence_boost,
            suggested_actions=suggested_actions,
            related_documentation=related_docs
        )
    
    async def get_service_recommendations(self, requirements: str, agent_type: str,
                                        context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get GCP service recommendations tailored for the agent type"""
        # Enhance requirements based on agent perspective
        agent_enhanced_requirements = self._enhance_requirements_for_agent(
            requirements, agent_type
        )
        
        # Get recommendations from RAG system
        if hasattr(self.rag_system, 'get_service_recommendations'):
            recommendations = await self.rag_system.get_service_recommendations(
                agent_enhanced_requirements
            )
            
            # Add agent-specific insights
            for rec in recommendations.get('recommendations', []):
                rec['agent_perspective'] = self._add_agent_perspective(rec, agent_type)
            
            return recommendations.get('recommendations', [])
        
        return []
    
    async def validate_best_practices(self, proposal: str, domain: str,
                                    agent_type: str) -> Dict[str, Any]:
        """Validate proposal against GCP best practices"""
        validation_query = f"Validate this {domain} approach against GCP best practices: {proposal}"
        
        rag_query = RAGQuery(
            query=validation_query,
            query_type="architecture" if agent_type == "architect" else "general",
            context={'domain': domain, 'agent_type': agent_type},
            max_context_chunks=4
        )
        
        response = await self.rag_system.query(rag_query)
        
        # Extract validation results
        validation_results = {
            'is_valid': self._assess_validation(response.answer),
            'best_practice_violations': self._extract_violations(response.answer),
            'recommendations': self._extract_recommendations(response.answer),
            'confidence': response.confidence,
            'supporting_sources': [
                {'title': source.title, 'url': source.url} 
                for source in response.sources
            ]
        }
        
        return validation_results
    
    def _enhance_query_for_agent(self, query: str, agent_type: str, query_type: str) -> str:
        """Enhance query based on agent type and context"""
        templates = self.agent_query_templates.get(agent_type, {})
        template = templates.get(query_type)
        
        if template:
            return template.format(query=query)
        
        # Default enhancement based on agent type
        agent_prefixes = {
            'architect': "From an architecture perspective, ",
            'developer': "For implementation purposes, ",
            'qa': "From a quality assurance standpoint, ",
            'scout': "For codebase analysis, ",
            'po': "From a product management perspective, "
        }
        
        prefix = agent_prefixes.get(agent_type, "")
        return f"{prefix}{query}"
    
    def _get_context_chunks_for_agent(self, agent_type: str) -> int:
        """Get optimal number of context chunks for each agent type"""
        chunk_counts = {
            'architect': 6,  # Needs comprehensive architectural context
            'developer': 4,  # Needs implementation details
            'qa': 3,         # Focused on testing approaches
            'scout': 5,      # Needs broad codebase understanding
            'po': 3          # Focused on business context
        }
        
        return chunk_counts.get(agent_type, 4)
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key GCP-related concepts from text"""
        # Common GCP services and concepts
        gcp_concepts = [
            'cloud run', 'kubernetes', 'gke', 'compute engine', 'app engine',
            'cloud storage', 'bigquery', 'cloud sql', 'firestore', 'bigtable',
            'vertex ai', 'cloud functions', 'pub/sub', 'cloud scheduler',
            'load balancing', 'vpc', 'iam', 'cloud build', 'cloud deploy',
            'monitoring', 'logging', 'cloud armor', 'cloud cdn'
        ]
        
        found_concepts = []
        text_lower = text.lower()
        
        for concept in gcp_concepts:
            if concept in text_lower:
                found_concepts.append(concept)
        
        return found_concepts[:5]  # Return top 5 concepts
    
    def _generate_agent_actions(self, response: str, agent_type: str) -> List[str]:
        """Generate suggested actions based on agent type and response"""
        base_actions = {
            'architect': [
                "Review the proposed architecture for scalability",
                "Validate security and compliance requirements",
                "Consider cost optimization opportunities"
            ],
            'developer': [
                "Implement proper error handling",
                "Add comprehensive logging and monitoring",
                "Write unit and integration tests"
            ],
            'qa': [
                "Create test cases for edge scenarios",
                "Set up automated regression testing",
                "Validate performance requirements"
            ],
            'scout': [
                "Check for code duplication opportunities",
                "Analyze dependency impacts",
                "Document technical debt findings"
            ],
            'po': [
                "Validate against user acceptance criteria",
                "Assess impact on product roadmap",
                "Calculate ROI and business value"
            ]
        }
        
        return base_actions.get(agent_type, [
            "Review the implementation approach",
            "Consider best practices and standards",
            "Document decisions and rationale"
        ])
    
    def _enhance_response_text(self, response: str, evidence: List[Dict[str, Any]]) -> str:
        """Enhance response text with supporting evidence"""
        if not evidence:
            return response
        
        enhanced = response
        
        # Add evidence references
        enhanced += "\n\n**Supporting Documentation:**\n"
        for item in evidence:
            enhanced += f"- [{item['title']}]({item['url']}) - {item['snippet']}\n"
        
        return enhanced
    
    def _enhance_requirements_for_agent(self, requirements: str, agent_type: str) -> str:
        """Enhance requirements with agent-specific considerations"""
        enhancements = {
            'architect': " considering scalability, security, and cost optimization",
            'developer': " focusing on implementation feasibility and maintainability",
            'qa': " emphasizing testability and quality assurance",
            'scout': " considering existing codebase integration and technical debt",
            'po': " focusing on business value and user impact"
        }
        
        enhancement = enhancements.get(agent_type, "")
        return f"{requirements}{enhancement}"
    
    def _add_agent_perspective(self, recommendation: Dict[str, Any], agent_type: str) -> str:
        """Add agent-specific perspective to service recommendations"""
        perspectives = {
            'architect': f"From an architecture standpoint, {recommendation['service']} provides enterprise-grade scalability and reliability.",
            'developer': f"For developers, {recommendation['service']} offers robust APIs and SDK support for rapid implementation.",
            'qa': f"From a QA perspective, {recommendation['service']} includes built-in monitoring and testing capabilities.",
            'scout': f"Considering codebase integration, {recommendation['service']} has minimal dependencies and good compatibility.",
            'po': f"From a business perspective, {recommendation['service']} offers strong ROI through its managed nature and scalability."
        }
        
        return perspectives.get(agent_type, f"{recommendation['service']} is well-suited for this use case.")
    
    def _assess_validation(self, response: str) -> bool:
        """Assess if the validation response indicates compliance with best practices"""
        positive_indicators = ['best practice', 'recommended', 'good approach', 'compliant', 'secure']
        negative_indicators = ['avoid', 'not recommended', 'security risk', 'deprecated', 'anti-pattern']
        
        response_lower = response.lower()
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in response_lower)
        negative_score = sum(1 for indicator in negative_indicators if indicator in response_lower)
        
        return positive_score > negative_score
    
    def _extract_violations(self, response: str) -> List[str]:
        """Extract best practice violations from response"""
        violations = []
        
        # Look for common violation patterns
        violation_patterns = [
            r'should not (.+?)[\.\n]',
            r'avoid (.+?)[\.\n]',
            r'security risk(.+?)[\.\n]',
            r'not recommended(.+?)[\.\n]'
        ]
        
        import re
        for pattern in violation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            violations.extend(matches[:2])  # Limit to 2 per pattern
        
        return violations[:5]  # Maximum 5 violations
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response"""
        recommendations = []
        
        # Look for recommendation patterns
        rec_patterns = [
            r'should (.+?)[\.\n]',
            r'recommend (.+?)[\.\n]',
            r'best practice(.+?)[\.\n]',
            r'consider (.+?)[\.\n]'
        ]
        
        import re
        for pattern in rec_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            recommendations.extend(matches[:2])  # Limit to 2 per pattern
        
        return recommendations[:5]  # Maximum 5 recommendations

# Factory function
def create_agent_knowledge_provider(rag_system: EnterpriseRAGSystem) -> AgentKnowledgeProvider:
    """Create an agent knowledge provider"""
    return AgentKnowledgeProvider(rag_system)