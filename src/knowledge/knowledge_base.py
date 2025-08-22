"""
Knowledge Base Implementation for Gemini Enterprise Architect
Provides intelligent documentation access and GCP service recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import requests
from bs4 import BeautifulSoup
import re

try:
    from google.cloud import aiplatform
    from google.cloud import storage
    import vertexai
    from vertexai.language_models import TextEmbeddingModel, TextGenerationModel
except ImportError:
    aiplatform = None
    storage = None
    vertexai = None
    TextEmbeddingModel = None
    TextGenerationModel = None

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of documentation with metadata"""
    content: str
    title: str
    url: str
    service: str
    category: str
    last_updated: datetime
    embedding: Optional[List[float]] = None
    chunk_id: str = field(default_factory=lambda: hashlib.md5().hexdigest()[:8])
    confidence_score: float = 0.0

@dataclass
class KnowledgeQuery:
    """Represents a query to the knowledge base"""
    query: str
    context: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 5
    similarity_threshold: float = 0.7

class GCPDocumentationScraper:
    """Scrapes and processes GCP documentation"""
    
    def __init__(self):
        self.base_urls = [
            "https://cloud.google.com/docs",
            "https://cloud.google.com/architecture",
            "https://cloud.google.com/solutions"
        ]
        self.service_patterns = {
            'compute': ['compute-engine', 'kubernetes', 'cloud-run', 'app-engine'],
            'storage': ['cloud-storage', 'filestore', 'persistent-disk'],
            'database': ['cloud-sql', 'firestore', 'bigtable', 'spanner'],
            'ai': ['vertex-ai', 'automl', 'natural-language', 'vision'],
            'networking': ['vpc', 'cloud-dns', 'cloud-cdn', 'load-balancing'],
            'security': ['cloud-iam', 'cloud-kms', 'security-center'],
            'analytics': ['bigquery', 'dataflow', 'pub-sub', 'cloud-composer']
        }
        
    async def scrape_service_docs(self, service: str) -> List[DocumentChunk]:
        """Scrape documentation for a specific GCP service"""
        chunks = []
        
        try:
            patterns = self.service_patterns.get(service, [service])
            
            for pattern in patterns:
                url = f"https://cloud.google.com/docs/{pattern}"
                
                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract main content
                content_div = soup.find('div', class_='devsite-article-body')
                if not content_div:
                    continue
                
                # Process content sections
                sections = content_div.find_all(['h1', 'h2', 'h3', 'p', 'div', 'code'])
                current_section = ""
                current_content = []
                
                for element in sections:
                    if element.name in ['h1', 'h2', 'h3']:
                        if current_content:
                            chunk = self._create_chunk(
                                '\n'.join(current_content),
                                current_section or element.get_text().strip(),
                                url,
                                service
                            )
                            if chunk:
                                chunks.append(chunk)
                            current_content = []
                        current_section = element.get_text().strip()
                    else:
                        text = element.get_text().strip()
                        if text and len(text) > 20:
                            current_content.append(text)
                
                # Add final chunk
                if current_content:
                    chunk = self._create_chunk(
                        '\n'.join(current_content),
                        current_section,
                        url,
                        service
                    )
                    if chunk:
                        chunks.append(chunk)
                        
        except Exception as e:
            logger.error(f"Error scraping {service} docs: {e}")
            
        return chunks
    
    def _create_chunk(self, content: str, title: str, url: str, service: str) -> Optional[DocumentChunk]:
        """Create a document chunk with metadata"""
        if len(content.strip()) < 50:
            return None
            
        # Clean content
        content = re.sub(r'\s+', ' ', content.strip())
        content = re.sub(r'[^\w\s\.\-\_\(\)\[\]\{\}\/\:\;,]', '', content)
        
        # Determine category
        category = "general"
        if any(word in content.lower() for word in ['best practice', 'recommendation']):
            category = "best_practices"
        elif any(word in content.lower() for word in ['example', 'tutorial', 'quickstart']):
            category = "examples"
        elif any(word in content.lower() for word in ['api', 'reference']):
            category = "api_reference"
        elif any(word in content.lower() for word in ['troubleshoot', 'error', 'debug']):
            category = "troubleshooting"
            
        return DocumentChunk(
            content=content,
            title=title,
            url=url,
            service=service,
            category=category,
            last_updated=datetime.now()
        )

class VertexAIKnowledgeStore:
    """Manages knowledge storage and retrieval using Vertex AI"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.embedding_model = None
        self.generation_model = None
        self.chunks: Dict[str, DocumentChunk] = {}
        self.embeddings_cache: Dict[str, List[float]] = {}
        
        if vertexai:
            vertexai.init(project=project_id, location=region)
            self.embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
            self.generation_model = TextGenerationModel.from_pretrained("text-bison@002")
    
    async def store_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Store document chunks with embeddings"""
        if not self.embedding_model:
            logger.warning("Vertex AI not available, storing chunks without embeddings")
            for chunk in chunks:
                self.chunks[chunk.chunk_id] = chunk
            return
            
        for chunk in chunks:
            try:
                # Generate embedding
                embeddings = self.embedding_model.get_embeddings([chunk.content])
                if embeddings:
                    chunk.embedding = embeddings[0].values
                    self.embeddings_cache[chunk.chunk_id] = chunk.embedding
                
                self.chunks[chunk.chunk_id] = chunk
                
            except Exception as e:
                logger.error(f"Error storing chunk {chunk.chunk_id}: {e}")
                # Store without embedding as fallback
                self.chunks[chunk.chunk_id] = chunk
    
    async def query(self, query: KnowledgeQuery) -> List[DocumentChunk]:
        """Query the knowledge base for relevant chunks"""
        if not self.chunks:
            return []
            
        # Generate query embedding if possible
        query_embedding = None
        if self.embedding_model:
            try:
                embeddings = self.embedding_model.get_embeddings([query.query])
                if embeddings:
                    query_embedding = embeddings[0].values
            except Exception as e:
                logger.error(f"Error generating query embedding: {e}")
        
        # Score and rank chunks
        scored_chunks = []
        for chunk in self.chunks.values():
            score = self._calculate_relevance_score(chunk, query, query_embedding)
            
            if score >= query.similarity_threshold:
                chunk.confidence_score = score
                scored_chunks.append(chunk)
        
        # Sort by score and apply filters
        scored_chunks.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Apply filters
        if query.filters:
            scored_chunks = self._apply_filters(scored_chunks, query.filters)
        
        return scored_chunks[:query.max_results]
    
    def _calculate_relevance_score(self, chunk: DocumentChunk, query: KnowledgeQuery, 
                                 query_embedding: Optional[List[float]]) -> float:
        """Calculate relevance score for a chunk"""
        score = 0.0
        
        # Semantic similarity (if embeddings available)
        if query_embedding and chunk.embedding:
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            score += similarity * 0.6
        
        # Text-based scoring
        query_words = set(query.query.lower().split())
        chunk_words = set(chunk.content.lower().split())
        
        # Keyword overlap
        overlap = len(query_words.intersection(chunk_words))
        if overlap > 0:
            score += (overlap / len(query_words)) * 0.3
        
        # Title relevance
        title_words = set(chunk.title.lower().split())
        title_overlap = len(query_words.intersection(title_words))
        if title_overlap > 0:
            score += (title_overlap / len(query_words)) * 0.1
        
        # Context matching
        if query.context:
            service_match = query.context.get('service') == chunk.service
            category_match = query.context.get('category') == chunk.category
            if service_match:
                score += 0.1
            if category_match:
                score += 0.05
        
        # Recency bonus
        days_old = (datetime.now() - chunk.last_updated).days
        if days_old < 30:
            score += 0.05
        
        return min(score, 1.0)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _apply_filters(self, chunks: List[DocumentChunk], filters: Dict[str, Any]) -> List[DocumentChunk]:
        """Apply filters to chunk results"""
        filtered = chunks
        
        if 'service' in filters:
            filtered = [c for c in filtered if c.service == filters['service']]
            
        if 'category' in filters:
            filtered = [c for c in filtered if c.category == filters['category']]
            
        if 'min_confidence' in filters:
            filtered = [c for c in filtered if c.confidence_score >= filters['min_confidence']]
            
        return filtered

class EnterpriseKnowledgeBase:
    """Main knowledge base interface for Gemini Enterprise Architect"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.scraper = GCPDocumentationScraper()
        self.store = VertexAIKnowledgeStore(project_id, region)
        self.last_update: Dict[str, datetime] = {}
        self.update_frequency = timedelta(days=7)  # Weekly updates
        
    async def initialize(self) -> None:
        """Initialize the knowledge base with core GCP documentation"""
        logger.info("Initializing Gemini Enterprise Knowledge Base...")
        
        # Core services to prioritize
        core_services = ['compute', 'storage', 'database', 'ai', 'networking', 'security']
        
        for service in core_services:
            if self._needs_update(service):
                logger.info(f"Updating documentation for {service}...")
                chunks = await self.scraper.scrape_service_docs(service)
                await self.store.store_chunks(chunks)
                self.last_update[service] = datetime.now()
                
                # Rate limiting
                await asyncio.sleep(2)
        
        logger.info(f"Knowledge base initialized with {len(self.store.chunks)} chunks")
    
    async def query_knowledge(self, query_text: str, context: Dict[str, Any] = None,
                            max_results: int = 5) -> List[DocumentChunk]:
        """Query the knowledge base for relevant information"""
        query = KnowledgeQuery(
            query=query_text,
            context=context or {},
            max_results=max_results,
            similarity_threshold=0.6
        )
        
        return await self.store.query(query)
    
    async def get_service_recommendations(self, requirements: str, 
                                        constraints: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get GCP service recommendations based on requirements"""
        # Query for relevant services
        chunks = await self.query_knowledge(
            f"GCP services for {requirements}",
            context={'category': 'best_practices'},
            max_results=10
        )
        
        # Analyze and rank services
        recommendations = []
        service_scores = {}
        
        for chunk in chunks:
            service = chunk.service
            score = chunk.confidence_score
            
            if service not in service_scores:
                service_scores[service] = {
                    'service': service,
                    'total_score': 0.0,
                    'evidence_count': 0,
                    'best_practices': [],
                    'examples': []
                }
            
            service_scores[service]['total_score'] += score
            service_scores[service]['evidence_count'] += 1
            
            if chunk.category == 'best_practices':
                service_scores[service]['best_practices'].append(chunk.content[:200])
            elif chunk.category == 'examples':
                service_scores[service]['examples'].append(chunk.content[:200])
        
        # Calculate final scores and create recommendations
        for service_data in service_scores.values():
            if service_data['evidence_count'] > 0:
                avg_score = service_data['total_score'] / service_data['evidence_count']
                
                recommendation = {
                    'service': service_data['service'],
                    'confidence': avg_score,
                    'evidence_count': service_data['evidence_count'],
                    'best_practices': service_data['best_practices'][:3],
                    'examples': service_data['examples'][:2],
                    'rationale': f"Based on {service_data['evidence_count']} relevant documentation chunks"
                }
                
                recommendations.append(recommendation)
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:5]
    
    async def scrape_and_add_document(self, url: str):
        """Scrape a URL and add its content to the knowledge base"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                content = soup.get_text(separator='\\n', strip=True)
                title = soup.title.string if soup.title else url
                
                chunks = self._create_chunk(content, title, url, "scraped")
                if chunks:
                    await self.store.store_chunks([chunks])
                    self.last_update[url] = datetime.now()
        except Exception as e:
            logger.error(f"Error scraping and adding document from {url}: {e}")

    def _needs_update(self, service: str) -> bool:
        """Check if service documentation needs updating"""
        if service not in self.last_update:
            return True
        
        return datetime.now() - self.last_update[service] > self.update_frequency
    
    async def update_service_docs(self, service: str) -> None:
        """Update documentation for a specific service"""
        logger.info(f"Updating {service} documentation...")
        chunks = await self.scraper.scrape_service_docs(service)
        await self.store.store_chunks(chunks)
        self.last_update[service] = datetime.now()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        services = {}
        categories = {}
        
        for chunk in self.store.chunks.values():
            services[chunk.service] = services.get(chunk.service, 0) + 1
            categories[chunk.category] = categories.get(chunk.category, 0) + 1
        
        return {
            'total_chunks': len(self.store.chunks),
            'services': services,
            'categories': categories,
            'last_updates': self.last_update,
            'has_embeddings': bool(self.store.embedding_model)
        }

# Factory function for easy initialization
async def create_knowledge_base(project_id: str, region: str = "us-central1") -> EnterpriseKnowledgeBase:
    """Create and initialize an enterprise knowledge base"""
    kb = EnterpriseKnowledgeBase(project_id, region)
    await kb.initialize()
    return kb