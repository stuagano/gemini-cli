"""
Knowledge System for Gemini Enterprise Architect
Provides intelligent knowledge integration for all agents
"""

from .knowledge_base import (
    EnterpriseKnowledgeBase,
    DocumentChunk,
    KnowledgeQuery,
    create_knowledge_base
)

from .vector_store import (
    EnterpriseVectorStore,
    VectorDocument,
    SearchResult,
    create_vector_store
)

from .rag_system import (
    EnterpriseRAGSystem,
    RAGQuery,
    RAGResponse,
    create_rag_system
)

from .integration import (
    KnowledgeIntegrationMixin,
    AgentKnowledgeProvider,
    create_agent_knowledge_provider
)

__all__ = [
    'EnterpriseKnowledgeBase',
    'DocumentChunk',
    'KnowledgeQuery',
    'create_knowledge_base',
    'EnterpriseVectorStore', 
    'VectorDocument',
    'SearchResult',
    'create_vector_store',
    'EnterpriseRAGSystem',
    'RAGQuery',
    'RAGResponse',
    'create_rag_system',
    'KnowledgeIntegrationMixin',
    'AgentKnowledgeProvider',
    'create_agent_knowledge_provider'
]