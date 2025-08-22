"""
RAG (Retrieval-Augmented Generation) System for Gemini Enterprise Architect
Combines knowledge retrieval with intelligent response generation
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re
from pathlib import Path

from .knowledge_base import EnterpriseKnowledgeBase, DocumentChunk
from .vector_store import EnterpriseVectorStore, SearchResult

try:
    from google.cloud import aiplatform
    import vertexai
    from vertexai.preview.generative_models import GenerativeModel, Part
    from vertexai.language_models import TextGenerationModel, CodeGenerationModel
except ImportError:
    aiplatform = None
    vertexai = None
    GenerativeModel = None
    Part = None
    TextGenerationModel = None
    CodeGenerationModel = None

logger = logging.getLogger(__name__)

@dataclass
class RAGQuery:
    """Represents a query for the RAG system"""
    query: str
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: str = ""
    session_id: str = ""
    query_type: str = "general"  # general, code, architecture, troubleshooting
    max_context_chunks: int = 5
    temperature: float = 0.3
    include_sources: bool = True

@dataclass
class RAGResponse:
    """Response from the RAG system"""
    answer: str
    sources: List[DocumentChunk]
    confidence: float
    query_id: str
    response_time_ms: int
    reasoning: str = ""
    suggested_followups: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'query_id': self.query_id,
            'response_time_ms': self.response_time_ms,
            'reasoning': self.reasoning,
            'suggested_followups': self.suggested_followups,
            'sources': [
                {
                    'title': source.title,
                    'url': source.url,
                    'service': source.service,
                    'category': source.category,
                    'snippet': source.content[:200] + '...' if len(source.content) > 200 else source.content
                }
                for source in self.sources
            ]
        }

class PromptTemplateManager:
    """Manages different prompt templates for various query types"""
    
    def __init__(self):
        self.templates = {
            'general': """You are an expert Google Cloud Platform architect with deep knowledge of GCP services, best practices, and enterprise implementations. Based on the provided context, answer the user's question accurately and comprehensively.

Context Documents:
{context}

User Question: {query}

Instructions:
- Provide a detailed, accurate answer based on the context
- Reference specific GCP services and features when relevant
- Include best practices and recommendations
- If the context doesn't contain sufficient information, clearly state what's missing
- Maintain a professional, helpful tone

Answer:""",

            'code': """You are a senior Google Cloud Platform developer specializing in cloud-native applications. Based on the provided context and documentation, help the user with their code-related question.

Context Documents:
{context}

User Question: {query}

Instructions:
- Provide working, production-ready code examples when requested
- Include proper error handling and best practices
- Reference official GCP SDKs and libraries
- Explain any complex concepts or patterns used
- Include comments in code for clarity
- Consider security, performance, and cost implications

Answer:""",

            'architecture': """You are a principal Google Cloud Platform architect with extensive experience in enterprise-scale deployments. Based on the provided context, provide architectural guidance.

Context Documents:
{context}

User Question: {query}

Instructions:
- Focus on scalable, reliable, and cost-effective solutions
- Consider enterprise requirements (security, compliance, governance)
- Recommend appropriate GCP services for the use case
- Address potential challenges and mitigation strategies
- Include deployment and operational considerations
- Provide clear rationale for architectural decisions

Answer:""",

            'troubleshooting': """You are a Google Cloud Platform support engineer with deep troubleshooting expertise. Based on the provided context, help diagnose and resolve the user's issue.

Context Documents:
{context}

User Question: {query}

Instructions:
- Provide step-by-step troubleshooting guidance
- Include specific commands, configurations, or tools to use
- Explain the likely root causes of the issue
- Suggest preventive measures to avoid recurrence
- Reference relevant GCP documentation and tools
- Prioritize solutions by likelihood of success

Answer:"""
        }
    
    def get_template(self, query_type: str) -> str:
        """Get the appropriate template for the query type"""
        return self.templates.get(query_type, self.templates['general'])
    
    def format_prompt(self, template: str, query: str, context_chunks: List[DocumentChunk],
                     additional_context: Dict[str, Any] = None) -> str:
        """Format the prompt with query and context"""
        # Format context documents
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            context_part = f"""Document {i} - {chunk.title} ({chunk.service})
Source: {chunk.url}
Category: {chunk.category}
Content: {chunk.content[:1000]}{'...' if len(chunk.content) > 1000 else ''}
"""
            context_parts.append(context_part)
        
        context_text = '\n'.join(context_parts) if context_parts else "No relevant context found."
        
        # Add additional context if provided
        if additional_context:
            context_text += f"\n\nAdditional Context:\n{json.dumps(additional_context, indent=2)}"
        
        return template.format(
            query=query,
            context=context_text
        )

class ResponseEnhancer:
    """Enhances RAG responses with additional intelligence"""
    
    def __init__(self):
        self.follow_up_patterns = {
            'code': [
                "How can I test this implementation?",
                "What are the security considerations?",
                "How can I optimize this for production?",
                "What monitoring should I add?"
            ],
            'architecture': [
                "What are the cost implications?",
                "How does this scale?",
                "What are the security requirements?",
                "How do I implement disaster recovery?"
            ],
            'troubleshooting': [
                "How can I prevent this issue in the future?",
                "What monitoring alerts should I set up?",
                "Are there any related issues I should check?",
                "What documentation should I reference?"
            ]
        }
    
    def enhance_response(self, response: str, query_type: str, sources: List[DocumentChunk]) -> Tuple[str, List[str]]:
        """Enhance the response with additional information and follow-ups"""
        enhanced_response = response
        
        # Add source references if they contain specific examples
        code_examples = []
        for source in sources:
            if 'example' in source.category.lower() or any(
                keyword in source.content.lower() 
                for keyword in ['```', 'gcloud', 'import ', 'def ', 'class ']
            ):
                code_examples.append(source.title)
        
        if code_examples:
            enhanced_response += f"\n\n**Additional Resources with Examples:**\n"
            for example in code_examples[:3]:
                enhanced_response += f"- {example}\n"
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(query_type, response, sources)
        
        return enhanced_response, follow_ups
    
    def _generate_follow_ups(self, query_type: str, response: str, sources: List[DocumentChunk]) -> List[str]:
        """Generate relevant follow-up questions"""
        base_follow_ups = self.follow_up_patterns.get(query_type, [])
        
        # Customize based on response content
        custom_follow_ups = []
        
        if 'cloud run' in response.lower():
            custom_follow_ups.append("How do I configure Cloud Run for production workloads?")
        if 'kubernetes' in response.lower():
            custom_follow_ups.append("What are the GKE best practices for this use case?")
        if 'bigquery' in response.lower():
            custom_follow_ups.append("How can I optimize BigQuery costs for this scenario?")
        if 'storage' in response.lower():
            custom_follow_ups.append("What are the different Cloud Storage classes I should consider?")
        
        # Combine and limit
        all_follow_ups = custom_follow_ups + base_follow_ups
        return all_follow_ups[:4]
    
    def calculate_confidence(self, sources: List[DocumentChunk], query: str) -> float:
        """Calculate confidence score for the response"""
        if not sources:
            return 0.0
        
        # Base confidence on source relevance
        relevance_scores = [getattr(source, 'confidence_score', 0.8) for source in sources]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        # Bonus for multiple high-quality sources
        quality_bonus = min(0.2, len(sources) * 0.05)
        
        # Bonus for official documentation
        official_bonus = 0.1 if any('cloud.google.com' in getattr(source, 'url', '') for source in sources) else 0.0
        
        # Penalty for very short or very long responses
        length_penalty = 0.0  # Would need actual response length
        
        confidence = min(1.0, avg_relevance + quality_bonus + official_bonus - length_penalty)
        return round(confidence, 2)

class EnterpriseRAGSystem:
    """Main RAG system combining knowledge retrieval and response generation"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.knowledge_base: Optional[EnterpriseKnowledgeBase] = None
        self.vector_store: Optional[EnterpriseVectorStore] = None
        self.generation_model = None
        self.code_model = None
        
        self.prompt_manager = PromptTemplateManager()
        self.response_enhancer = ResponseEnhancer()
        
        # Performance tracking
        self.query_cache: Dict[str, RAGResponse] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Initialize models
        if vertexai:
            vertexai.init(project=project_id, location=region)
            try:
                import os
                model_name = os.environ.get('VERTEX_AI_MODEL', 'gemini-1.5-pro')
                # Try the exact model name first
                try:
                    self.generation_model = GenerativeModel(model_name)
                    self.code_model = GenerativeModel(model_name)  # Same model, different prompts
                except:
                    # Fallback to common model names
                    self.generation_model = GenerativeModel("gemini-1.5-pro")
                    self.code_model = GenerativeModel("gemini-1.5-pro")
            except Exception as e:
                logger.error(f"Error initializing Vertex AI models: {e}")
                # Fallback to text models
                try:
                    self.generation_model = TextGenerationModel.from_pretrained("text-bison@002")
                    self.code_model = CodeGenerationModel.from_pretrained("code-bison@002")
                except Exception as e2:
                    logger.error(f"Error initializing fallback models: {e2}")
    
    async def initialize(self, vector_config: Dict[str, Any] = None) -> None:
        """Initialize the RAG system components"""
        logger.info("Initializing Enterprise RAG System...")
        
        # Initialize knowledge base
        self.knowledge_base = EnterpriseKnowledgeBase(self.project_id, self.region)
        await self.knowledge_base.initialize()
        
        # Initialize vector store if config provided
        if vector_config:
            from .vector_store import create_vector_store
            self.vector_store = create_vector_store(vector_config)
        
        logger.info("RAG System initialized successfully")
    
    async def query(self, rag_query: RAGQuery) -> RAGResponse:
        """Process a query through the RAG system"""
        start_time = datetime.now()
        query_id = f"rag_{hash(rag_query.query + str(start_time))}"
        
        try:
            # Check cache first
            cache_key = f"{rag_query.query}_{rag_query.query_type}_{rag_query.max_context_chunks}"
            if cache_key in self.query_cache:
                cached = self.query_cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cached.query_id.split('_')[-1]) < self.cache_ttl:
                    logger.info(f"Returning cached response for query: {rag_query.query[:50]}...")
                    return cached
            
            # Retrieve relevant context
            context_chunks = await self._retrieve_context(rag_query)
            
            # Generate response
            response_text = await self._generate_response(rag_query, context_chunks)
            
            # Enhance response
            enhanced_response, follow_ups = self.response_enhancer.enhance_response(
                response_text, rag_query.query_type, context_chunks
            )
            
            # Calculate confidence
            confidence = self.response_enhancer.calculate_confidence(context_chunks, rag_query.query)
            
            # Create response object
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            rag_response = RAGResponse(
                answer=enhanced_response,
                sources=context_chunks,
                confidence=confidence,
                query_id=query_id,
                response_time_ms=response_time,
                reasoning=f"Retrieved {len(context_chunks)} relevant documents and generated response using {rag_query.query_type} template",
                suggested_followups=follow_ups
            )
            
            # Cache the response
            self.query_cache[cache_key] = rag_response
            
            return rag_response
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            return RAGResponse(
                answer=f"I encountered an error while processing your query: {str(e)}. Please try rephrasing your question or contact support.",
                sources=[],
                confidence=0.0,
                query_id=query_id,
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                reasoning="Error occurred during processing"
            )
    
    async def _retrieve_context(self, rag_query: RAGQuery) -> List[DocumentChunk]:
        """Retrieve relevant context for the query"""
        context_chunks = []
        
        # Primary retrieval from knowledge base
        if self.knowledge_base:
            try:
                kb_chunks = await self.knowledge_base.query_knowledge(
                    rag_query.query,
                    context=rag_query.context,
                    max_results=rag_query.max_context_chunks
                )
                context_chunks.extend(kb_chunks)
            except Exception as e:
                logger.warning(f"Knowledge base retrieval failed: {e}")
        
        # Secondary retrieval from vector store
        if self.vector_store and len(context_chunks) < rag_query.max_context_chunks:
            try:
                remaining = rag_query.max_context_chunks - len(context_chunks)
                vector_results = await self.vector_store.search(
                    rag_query.query,
                    k=remaining,
                    filters=rag_query.context
                )
                
                # Convert search results to document chunks
                for result in vector_results:
                    context_chunks.append(result.document)
                    
            except Exception as e:
                logger.warning(f"Vector store retrieval failed: {e}")
        
        # Remove duplicates and sort by relevance
        unique_chunks = {}
        for chunk in context_chunks:
            chunk_key = f"{chunk.url}_{chunk.title}"
            if chunk_key not in unique_chunks:
                unique_chunks[chunk_key] = chunk
        
        final_chunks = list(unique_chunks.values())
        final_chunks.sort(key=lambda x: getattr(x, 'confidence_score', 0.5), reverse=True)
        
        return final_chunks[:rag_query.max_context_chunks]
    
    async def _generate_response(self, rag_query: RAGQuery, context_chunks: List[DocumentChunk]) -> str:
        """Generate response using the language model"""
        if not self.generation_model:
            return self._fallback_response(rag_query, context_chunks)
        
        try:
            # Get appropriate template
            template = self.prompt_manager.get_template(rag_query.query_type)
            
            # Format prompt
            prompt = self.prompt_manager.format_prompt(
                template, rag_query.query, context_chunks, rag_query.context
            )
            
            # Choose model based on query type
            model = self.code_model if rag_query.query_type == 'code' else self.generation_model
            
            # Generate response
            if hasattr(model, 'generate_content'):  # Gemini model
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': rag_query.temperature,
                        'max_output_tokens': 2048,
                        'top_p': 0.8,
                        'top_k': 40
                    }
                )
                return response.text
            else:  # Legacy text model
                response = model.predict(
                    prompt,
                    temperature=rag_query.temperature,
                    max_output_tokens=2048,
                    top_p=0.8,
                    top_k=40
                )
                return response.text
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(rag_query, context_chunks)
    
    def _fallback_response(self, rag_query: RAGQuery, context_chunks: List[DocumentChunk]) -> str:
        """Generate a fallback response when AI models are unavailable"""
        if not context_chunks:
            return "I don't have enough information to answer your question. Please try rephrasing or providing more context."
        
        # Simple template-based response
        response_parts = [
            f"Based on the available documentation, here's what I found regarding your question: {rag_query.query}\n"
        ]
        
        for i, chunk in enumerate(context_chunks[:3], 1):
            response_parts.append(f"\n**Source {i} - {chunk.title}:**")
            response_parts.append(chunk.content[:300] + ('...' if len(chunk.content) > 300 else ''))
            response_parts.append(f"Reference: {chunk.url}\n")
        
        response_parts.append("\nPlease refer to the official GCP documentation for the most up-to-date information.")
        
        return '\n'.join(response_parts)
    
    async def get_service_recommendations(self, requirements: str) -> Dict[str, Any]:
        """Get intelligent service recommendations"""
        if not self.knowledge_base:
            return {'error': 'Knowledge base not initialized'}
        
        recommendations = await self.knowledge_base.get_service_recommendations(requirements)
        
        # Enhance with RAG-generated explanations
        for rec in recommendations:
            try:
                query = RAGQuery(
                    query=f"Explain why {rec['service']} is suitable for {requirements}",
                    query_type="architecture",
                    max_context_chunks=3
                )
                rag_response = await self.query(query)
                rec['explanation'] = rag_response.answer[:500]
            except Exception as e:
                logger.warning(f"Could not generate explanation for {rec['service']}: {e}")
        
        return {
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat(),
            'requirements': requirements
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {
            'rag_system': {
                'project_id': self.project_id,
                'region': self.region,
                'has_generation_model': self.generation_model is not None,
                'has_code_model': self.code_model is not None,
                'cache_size': len(self.query_cache),
                'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600
            }
        }
        
        if self.knowledge_base:
            stats['knowledge_base'] = self.knowledge_base.get_knowledge_stats()
        
        if self.vector_store:
            stats['vector_store'] = self.vector_store.get_stats()
        
        return stats

# Factory function for easy initialization
async def create_rag_system(project_id: str, region: str = "us-central1",
                          vector_config: Dict[str, Any] = None) -> EnterpriseRAGSystem:
    """Create and initialize an Enterprise RAG System"""
    rag = EnterpriseRAGSystem(project_id, region)
    await rag.initialize(vector_config)
    return rag