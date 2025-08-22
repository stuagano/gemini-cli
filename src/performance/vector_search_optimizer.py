"""
Performance Optimization - Vector Search Optimizer
Implements efficient vector search for knowledge retrieval
Epic 7: Story 7.2 - Knowledge Retrieval Optimization
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import faiss
import pickle

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Document with vector embedding"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    timestamp: datetime

class VectorSearchOptimizer:
    """Optimized vector search for RAG knowledge retrieval"""
    
    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "IVF",
        nlist: int = 100,
        nprobe: int = 10,
        cache_embeddings: bool = True
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.nprobe = nprobe
        self.cache_embeddings = cache_embeddings
        
        # Initialize index
        self.index = self._create_index()
        self.documents = {}
        self.id_to_index = {}
        self.embedding_cache = {}
        
        # Performance metrics
        self.metrics = {
            'searches': 0,
            'avg_search_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'index_size': 0
        }
    
    def _create_index(self) -> faiss.Index:
        """Create optimized FAISS index"""
        if self.index_type == "IVF":
            # IVF index for large datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
        elif self.index_type == "HNSW":
            # HNSW for high recall
            index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            # Simple flat index for small datasets
            index = faiss.IndexFlatL2(self.dimension)
        
        return index
    
    def train_index(self, training_vectors: np.ndarray):
        """Train the index with sample vectors"""
        if hasattr(self.index, 'train'):
            logger.info(f"Training index with {len(training_vectors)} vectors")
            self.index.train(training_vectors)
            self.index.nprobe = self.nprobe
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: Optional[np.ndarray] = None
    ):
        """Add documents to the index"""
        if embeddings is None:
            embeddings = await self._generate_embeddings(documents)
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Store document metadata
        for i, doc in enumerate(documents):
            doc_id = doc.get('id', str(start_idx + i))
            self.documents[doc_id] = VectorDocument(
                id=doc_id,
                content=doc['content'],
                embedding=embeddings[i],
                metadata=doc.get('metadata', {}),
                timestamp=datetime.now()
            )
            self.id_to_index[doc_id] = start_idx + i
        
        self.metrics['index_size'] = self.index.ntotal
        logger.info(f"Added {len(documents)} documents to index")
    
    async def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[VectorDocument, float]]:
        """Search for similar documents"""
        start_time = time.time()
        self.metrics['searches'] += 1
        
        # Get query embedding
        query_embedding = await self._get_query_embedding(query)
        
        # Search in FAISS
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), k * 2  # Get extra for filtering
        )
        
        # Apply filters and collect results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            
            # Find document by index
            doc = self._get_document_by_index(idx)
            if doc and self._apply_filters(doc, filters):
                results.append((doc, float(dist)))
            
            if len(results) >= k:
                break
        
        # Update metrics
        search_time = time.time() - start_time
        self._update_search_metrics(search_time)
        
        logger.debug(f"Search completed in {search_time:.3f}s, found {len(results)} results")
        return results
    
    async def hybrid_search(
        self,
        query: str,
        k: int = 10,
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Tuple[VectorDocument, float]]:
        """Hybrid search combining vector and keyword search"""
        # Vector search
        vector_results = await self.search(query, k * 2)
        
        # Keyword search (BM25-style)
        keyword_results = self._keyword_search(query, k * 2)
        
        # Combine and rerank
        combined_scores = {}
        
        # Add vector search results
        for doc, score in vector_results:
            combined_scores[doc.id] = vector_weight * (1 / (1 + score))
        
        # Add keyword search results
        for doc, score in keyword_results:
            if doc.id in combined_scores:
                combined_scores[doc.id] += keyword_weight * score
            else:
                combined_scores[doc.id] = keyword_weight * score
        
        # Sort by combined score
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
        
        # Return documents with scores
        return [(self.documents[doc_id], score) for doc_id, score in sorted_results]
    
    def _keyword_search(
        self,
        query: str,
        k: int
    ) -> List[Tuple[VectorDocument, float]]:
        """Simple keyword search implementation"""
        query_terms = set(query.lower().split())
        scores = []
        
        for doc_id, doc in self.documents.items():
            content_terms = set(doc.content.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(query_terms & content_terms)
            union = len(query_terms | content_terms)
            
            if union > 0:
                score = intersection / union
                if score > 0:
                    scores.append((doc, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]
    
    async def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get or generate query embedding"""
        if self.cache_embeddings:
            cache_key = hashlib.md5(query.encode()).hexdigest()
            
            if cache_key in self.embedding_cache:
                self.metrics['cache_hits'] += 1
                return self.embedding_cache[cache_key]
            
            self.metrics['cache_misses'] += 1
        
        # Generate embedding (mock implementation)
        embedding = await self._generate_embedding(query)
        
        if self.cache_embeddings:
            self.embedding_cache[cache_key] = embedding
            
            # Limit cache size
            if len(self.embedding_cache) > 1000:
                # Remove oldest entries
                keys = list(self.embedding_cache.keys())[:100]
                for key in keys:
                    del self.embedding_cache[key]
        
        return embedding
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text (mock implementation)"""
        # In production, this would call an embedding model
        # For now, return a random vector
        await asyncio.sleep(0.01)  # Simulate API call
        return np.random.randn(self.dimension).astype('float32')
    
    async def _generate_embeddings(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """Generate embeddings for multiple documents"""
        embeddings = []
        for doc in documents:
            embedding = await self._generate_embedding(doc['content'])
            embeddings.append(embedding)
        return np.array(embeddings).astype('float32')
    
    def _get_document_by_index(self, idx: int) -> Optional[VectorDocument]:
        """Get document by FAISS index"""
        for doc_id, index in self.id_to_index.items():
            if index == idx:
                return self.documents.get(doc_id)
        return None
    
    def _apply_filters(
        self,
        doc: VectorDocument,
        filters: Optional[Dict[str, Any]]
    ) -> bool:
        """Apply metadata filters to document"""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in doc.metadata:
                return False
            
            if isinstance(value, list):
                if doc.metadata[key] not in value:
                    return False
            elif doc.metadata[key] != value:
                return False
        
        return True
    
    def _update_search_metrics(self, search_time: float):
        """Update search performance metrics"""
        current_avg = self.metrics['avg_search_time']
        total_searches = self.metrics['searches']
        
        self.metrics['avg_search_time'] = (
            (current_avg * (total_searches - 1) + search_time) / total_searches
        )
    
    def optimize_index(self):
        """Optimize index for better performance"""
        if hasattr(self.index, 'nprobe'):
            # Adjust nprobe based on performance
            if self.metrics['avg_search_time'] > 0.1:
                self.index.nprobe = max(1, self.index.nprobe - 1)
            elif self.metrics['avg_search_time'] < 0.01:
                self.index.nprobe = min(self.nlist, self.index.nprobe + 1)
        
        logger.info("Index optimized based on performance metrics")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_rate = 0
        if self.metrics['cache_hits'] + self.metrics['cache_misses'] > 0:
            cache_rate = self.metrics['cache_hits'] / (
                self.metrics['cache_hits'] + self.metrics['cache_misses']
            ) * 100
        
        return {
            'total_searches': self.metrics['searches'],
            'avg_search_time_ms': self.metrics['avg_search_time'] * 1000,
            'cache_hit_rate': f"{cache_rate:.2f}%",
            'index_size': self.metrics['index_size'],
            'index_type': self.index_type,
            'dimension': self.dimension
        }
    
    def save_index(self, path: str):
        """Save index to disk"""
        faiss.write_index(self.index, f"{path}.index")
        
        with open(f"{path}.meta", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'id_to_index': self.id_to_index,
                'metrics': self.metrics
            }, f)
        
        logger.info(f"Index saved to {path}")
    
    def load_index(self, path: str):
        """Load index from disk"""
        self.index = faiss.read_index(f"{path}.index")
        
        with open(f"{path}.meta", 'rb') as f:
            data = pickle.load(f)
            self.documents = data['documents']
            self.id_to_index = data['id_to_index']
            self.metrics = data['metrics']
        
        logger.info(f"Index loaded from {path}")

class RAGOptimizer:
    """Optimize RAG (Retrieval Augmented Generation) pipeline"""
    
    def __init__(
        self,
        vector_search: VectorSearchOptimizer,
        cache_responses: bool = True
    ):
        self.vector_search = vector_search
        self.cache_responses = cache_responses
        self.response_cache = {}
        
        # RAG metrics
        self.metrics = {
            'queries': 0,
            'avg_retrieval_time': 0,
            'avg_generation_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def query(
        self,
        question: str,
        k: int = 5,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """Execute RAG query with optimization"""
        start_time = time.time()
        self.metrics['queries'] += 1
        
        # Check response cache
        if self.cache_responses:
            cache_key = hashlib.md5(f"{question}:{k}".encode()).hexdigest()
            
            if cache_key in self.response_cache:
                self.metrics['cache_hits'] += 1
                return self.response_cache[cache_key]
            
            self.metrics['cache_misses'] += 1
        
        # Retrieve relevant documents
        retrieval_start = time.time()
        
        if use_hybrid:
            results = await self.vector_search.hybrid_search(question, k)
        else:
            results = await self.vector_search.search(question, k)
        
        retrieval_time = time.time() - retrieval_start
        
        # Prepare context
        context = self._prepare_context(results)
        
        # Generate response (mock)
        generation_start = time.time()
        response = await self._generate_response(question, context)
        generation_time = time.time() - generation_start
        
        # Update metrics
        self._update_metrics(retrieval_time, generation_time)
        
        # Prepare result
        result = {
            'answer': response,
            'sources': [
                {
                    'content': doc.content[:200],
                    'score': score,
                    'metadata': doc.metadata
                }
                for doc, score in results
            ],
            'metrics': {
                'retrieval_time_ms': retrieval_time * 1000,
                'generation_time_ms': generation_time * 1000,
                'total_time_ms': (time.time() - start_time) * 1000
            }
        }
        
        # Cache response
        if self.cache_responses:
            self.response_cache[cache_key] = result
            
            # Limit cache size
            if len(self.response_cache) > 100:
                keys = list(self.response_cache.keys())[:10]
                for key in keys:
                    del self.response_cache[key]
        
        return result
    
    def _prepare_context(
        self,
        results: List[Tuple[VectorDocument, float]]
    ) -> str:
        """Prepare context from search results"""
        context_parts = []
        
        for doc, score in results:
            # Add document content with relevance indicator
            relevance = "HIGH" if score < 0.5 else "MEDIUM" if score < 1.0 else "LOW"
            context_parts.append(
                f"[{relevance} RELEVANCE]\n{doc.content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    async def _generate_response(
        self,
        question: str,
        context: str
    ) -> str:
        """Generate response using context (mock implementation)"""
        # In production, this would call an LLM
        await asyncio.sleep(0.1)  # Simulate API call
        
        return f"Based on the provided context, here's the answer to '{question}': " \
               f"[Generated response using {len(context)} characters of context]"
    
    def _update_metrics(self, retrieval_time: float, generation_time: float):
        """Update RAG performance metrics"""
        queries = self.metrics['queries']
        
        # Update averages
        self.metrics['avg_retrieval_time'] = (
            (self.metrics['avg_retrieval_time'] * (queries - 1) + retrieval_time) / queries
        )
        self.metrics['avg_generation_time'] = (
            (self.metrics['avg_generation_time'] * (queries - 1) + generation_time) / queries
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get RAG performance statistics"""
        cache_rate = 0
        if self.metrics['cache_hits'] + self.metrics['cache_misses'] > 0:
            cache_rate = self.metrics['cache_hits'] / (
                self.metrics['cache_hits'] + self.metrics['cache_misses']
            ) * 100
        
        return {
            'total_queries': self.metrics['queries'],
            'avg_retrieval_time_ms': self.metrics['avg_retrieval_time'] * 1000,
            'avg_generation_time_ms': self.metrics['avg_generation_time'] * 1000,
            'cache_hit_rate': f"{cache_rate:.2f}%",
            'vector_search_stats': self.vector_search.get_performance_stats()
        }

class BatchProcessor:
    """Process embeddings and searches in batches for efficiency"""
    
    def __init__(
        self,
        batch_size: int = 32,
        max_queue_size: int = 1000
    ):
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self.processing_queue = asyncio.Queue(maxsize=max_queue_size)
        self.result_futures = {}
    
    async def process_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[np.ndarray]:
        """Process embeddings in batches"""
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Process batch (mock implementation)
            batch_embeddings = await self._generate_batch_embeddings(batch)
            embeddings.extend(batch_embeddings)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        return embeddings
    
    async def _generate_batch_embeddings(
        self,
        texts: List[str]
    ) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts"""
        # In production, this would call a batch embedding API
        await asyncio.sleep(0.05)  # Simulate API call
        return [np.random.randn(768).astype('float32') for _ in texts]

# Global instances
vector_optimizer = VectorSearchOptimizer()
rag_optimizer = RAGOptimizer(vector_optimizer)
batch_processor = BatchProcessor()

# Example usage
async def example_usage():
    """Example of using the vector search optimizer"""
    
    # Add sample documents
    documents = [
        {
            'id': 'doc1',
            'content': 'FastAPI is a modern web framework for building APIs.',
            'metadata': {'category': 'framework', 'language': 'python'}
        },
        {
            'id': 'doc2',
            'content': 'Redis is an in-memory data structure store.',
            'metadata': {'category': 'database', 'type': 'nosql'}
        },
        {
            'id': 'doc3',
            'content': 'Docker containers provide isolated environments.',
            'metadata': {'category': 'devops', 'type': 'containerization'}
        }
    ]
    
    await vector_optimizer.add_documents(documents)
    
    # Search for similar documents
    results = await vector_optimizer.search("web API development", k=2)
    
    for doc, score in results:
        print(f"Document: {doc.id}, Score: {score:.4f}")
    
    # RAG query
    response = await rag_optimizer.query(
        "What is FastAPI and how does it relate to web development?",
        k=3
    )
    
    print(f"Answer: {response['answer']}")
    print(f"Performance: {response['metrics']}")
    
    # Get performance stats
    print("Vector Search Stats:", vector_optimizer.get_performance_stats())
    print("RAG Stats:", rag_optimizer.get_performance_stats())