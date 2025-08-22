"""
Vector Database Implementation for Gemini Enterprise Architect
Provides high-performance embedding storage and retrieval using Vertex AI
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import asyncio
import logging
import json
import numpy as np
from dataclasses import dataclass, asdict
from datetime import datetime
import pickle
import os
from pathlib import Path

try:
    from google.cloud import aiplatform
    from google.cloud import storage
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    from vertexai.preview.generative_models import GenerativeModel
except ImportError:
    aiplatform = None
    storage = None
    vertexai = None
    TextEmbeddingModel = None
    GenerativeModel = None

try:
    import faiss
except ImportError:
    faiss = None

try:
    import pinecone
except ImportError:
    pinecone = None

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Document with vector embedding and metadata"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime
    source: str
    service: str
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'embedding': self.embedding,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'service': self.service,
            'category': self.category
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorDocument':
        return cls(
            id=data['id'],
            content=data['content'],
            embedding=data['embedding'],
            metadata=data['metadata'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            service=data['service'],
            category=data['category']
        )

@dataclass
class SearchResult:
    """Search result with similarity score"""
    document: VectorDocument
    similarity_score: float
    rank: int

class VertexAIEmbeddingProvider:
    """Manages embeddings using Vertex AI"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.model = None
        self.dimension = 768  # Default for text-embedding-gecko
        
        if vertexai:
            vertexai.init(project=project_id, location=region)
            # Use model from environment or default
            import os
            model_name = os.environ.get('VERTEX_AI_EMBEDDING_MODEL', 'text-embedding-004')
            # Map model names to vertex AI model IDs
            model_map = {
                'text-embedding-004': 'text-embedding-004',
                'textembedding-gecko': 'textembedding-gecko@003',
                'textembedding-gecko@003': 'textembedding-gecko@003'
            }
            model_id = model_map.get(model_name, model_name)
            try:
                self.model = TextEmbeddingModel.from_pretrained(model_id)
                # Update dimension based on model
                if 'text-embedding-004' in model_id:
                    self.dimension = 768
                elif 'gecko' in model_id:
                    self.dimension = 768
            except Exception as e:
                logger.warning(f"Failed to load model {model_id}: {e}, trying default")
                self.model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not self.model:
            logger.warning("Vertex AI not available, returning dummy embeddings")
            return [[0.0] * self.dimension for _ in texts]
        
        try:
            # Vertex AI has batch limits
            batch_size = 25
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.model.get_embeddings(batch)
                batch_embeddings = [emb.values for emb in embeddings]
                all_embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * self.dimension for _ in texts]
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

class FAISSVectorStore:
    """Local vector store using FAISS for fast similarity search"""
    
    def __init__(self, dimension: int = 768, index_type: str = "IVF"):
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.documents: Dict[str, VectorDocument] = {}
        self.id_to_index: Dict[str, int] = {}
        self.index_to_id: Dict[int, str] = {}
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize the FAISS index"""
        if not faiss:
            logger.warning("FAISS not available, using fallback implementation")
            return
        
        try:
            if self.index_type == "IVF":
                # IndexIVFFlat for larger datasets
                quantizer = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                # Simple flat index for smaller datasets
                self.index = faiss.IndexFlatIP(self.dimension)
                
        except Exception as e:
            logger.error(f"Error initializing FAISS index: {e}")
            self.index = None
    
    async def add_documents(self, documents: List[VectorDocument]) -> None:
        """Add documents to the vector store"""
        if not documents:
            return
        
        # Store documents in memory
        for doc in documents:
            self.documents[doc.id] = doc
        
        if not self.index or not faiss:
            logger.warning("FAISS index not available, storing documents without vector search")
            return
        
        try:
            # Prepare embeddings
            embeddings = np.array([doc.embedding for doc in documents], dtype=np.float32)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Get current index size
            current_size = self.index.ntotal
            
            # Train index if it's IVF and not trained
            if self.index_type == "IVF" and not self.index.is_trained:
                if len(embeddings) >= 100:  # Need enough data to train
                    self.index.train(embeddings)
                else:
                    # Switch to flat index for small datasets
                    self.index = faiss.IndexFlatIP(self.dimension)
            
            # Add to index
            self.index.add(embeddings)
            
            # Update ID mappings
            for i, doc in enumerate(documents):
                index_pos = current_size + i
                self.id_to_index[doc.id] = index_pos
                self.index_to_id[index_pos] = doc.id
                
        except Exception as e:
            logger.error(f"Error adding documents to FAISS index: {e}")
    
    async def search(self, query_embedding: List[float], k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for similar documents"""
        if not self.index or not faiss:
            # Fallback to simple text matching
            return await self._fallback_search(query_embedding, k, filters)
        
        try:
            # Normalize query embedding
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Search
            scores, indices = self.index.search(query_vector, min(k * 2, self.index.ntotal))
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # Invalid index
                    continue
                
                doc_id = self.index_to_id.get(idx)
                if not doc_id or doc_id not in self.documents:
                    continue
                
                doc = self.documents[doc_id]
                
                # Apply filters
                if filters and not self._matches_filters(doc, filters):
                    continue
                
                results.append(SearchResult(
                    document=doc,
                    similarity_score=float(score),
                    rank=len(results) + 1
                ))
                
                if len(results) >= k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching FAISS index: {e}")
            return await self._fallback_search(query_embedding, k, filters)
    
    async def _fallback_search(self, query_embedding: List[float], k: int,
                              filters: Dict[str, Any]) -> List[SearchResult]:
        """Fallback search using simple similarity calculation"""
        results = []
        
        for doc in self.documents.values():
            if filters and not self._matches_filters(doc, filters):
                continue
            
            similarity = self._cosine_similarity(query_embedding, doc.embedding)
            results.append(SearchResult(
                document=doc,
                similarity_score=similarity,
                rank=0
            ))
        
        # Sort by similarity
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results[:k]):
            result.rank = i + 1
        
        return results[:k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def _matches_filters(self, doc: VectorDocument, filters: Dict[str, Any]) -> bool:
        """Check if document matches the given filters"""
        for key, value in filters.items():
            if key == 'service' and doc.service != value:
                return False
            elif key == 'category' and doc.category != value:
                return False
            elif key == 'source' and doc.source != value:
                return False
            elif key in doc.metadata and doc.metadata[key] != value:
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_type': self.index_type,
            'has_faiss': faiss is not None,
            'is_trained': self.index.is_trained if self.index and hasattr(self.index, 'is_trained') else False
        }
    
    def save_to_disk(self, path: str) -> None:
        """Save the vector store to disk"""
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            
            # Save documents
            with open(f"{path}_documents.pkl", 'wb') as f:
                pickle.dump({
                    'documents': {id: doc.to_dict() for id, doc in self.documents.items()},
                    'id_to_index': self.id_to_index,
                    'index_to_id': self.index_to_id
                }, f)
            
            # Save FAISS index
            if self.index and faiss:
                faiss.write_index(self.index, f"{path}_faiss.index")
                
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def load_from_disk(self, path: str) -> None:
        """Load the vector store from disk"""
        try:
            # Try both naming conventions for compatibility
            doc_file = f"{path}_documents.pkl"
            if not os.path.exists(doc_file):
                doc_file = f"{path}_primary_documents.pkl"
            
            # Load documents
            with open(doc_file, 'rb') as f:
                data = pickle.load(f)
                self.documents = {
                    id: VectorDocument.from_dict(doc_dict) 
                    for id, doc_dict in data['documents'].items()
                }
                self.id_to_index = data['id_to_index']
                self.index_to_id = data['index_to_id']
            
            # Load FAISS index
            index_file = f"{path}_faiss.index"
            if not os.path.exists(index_file):
                index_file = f"{path}_primary_faiss.index"
            
            if faiss and os.path.exists(index_file):
                self.index = faiss.read_index(index_file)
            else:
                self._initialize_index()
                
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")

class PineconeVectorStore:
    """Cloud vector store using Pinecone"""
    
    def __init__(self, api_key: str, environment: str, index_name: str, dimension: int = 768):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = dimension
        self.index = None
        
        if pinecone:
            try:
                pinecone.init(api_key=api_key, environment=environment)
                
                # Create index if it doesn't exist
                if index_name not in pinecone.list_indexes():
                    pinecone.create_index(
                        index_name,
                        dimension=dimension,
                        metric='cosine'
                    )
                
                self.index = pinecone.Index(index_name)
                
            except Exception as e:
                logger.error(f"Error initializing Pinecone: {e}")
                self.index = None
    
    async def add_documents(self, documents: List[VectorDocument]) -> None:
        """Add documents to Pinecone"""
        if not self.index:
            logger.warning("Pinecone index not available")
            return
        
        try:
            # Prepare vectors for Pinecone
            vectors = []
            for doc in documents:
                vectors.append({
                    'id': doc.id,
                    'values': doc.embedding,
                    'metadata': {
                        'content': doc.content,
                        'service': doc.service,
                        'category': doc.category,
                        'source': doc.source,
                        'timestamp': doc.timestamp.isoformat(),
                        **doc.metadata
                    }
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                
                # Rate limiting
                if i + batch_size < len(vectors):
                    await asyncio.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error adding documents to Pinecone: {e}")
    
    async def search(self, query_embedding: List[float], k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search Pinecone for similar documents"""
        if not self.index:
            return []
        
        try:
            # Build filter for Pinecone
            pinecone_filter = {}
            if filters:
                for key, value in filters.items():
                    pinecone_filter[key] = {"$eq": value}
            
            # Search
            response = self.index.query(
                vector=query_embedding,
                top_k=k,
                include_metadata=True,
                filter=pinecone_filter if pinecone_filter else None
            )
            
            results = []
            for i, match in enumerate(response['matches']):
                metadata = match['metadata']
                
                doc = VectorDocument(
                    id=match['id'],
                    content=metadata.get('content', ''),
                    embedding=query_embedding,  # Pinecone doesn't return embeddings
                    metadata={k: v for k, v in metadata.items() 
                             if k not in ['content', 'service', 'category', 'source', 'timestamp']},
                    timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.now().isoformat())),
                    source=metadata.get('source', ''),
                    service=metadata.get('service', ''),
                    category=metadata.get('category', '')
                )
                
                results.append(SearchResult(
                    document=doc,
                    similarity_score=match['score'],
                    rank=i + 1
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []

class EnterpriseVectorStore:
    """Enterprise-grade vector store with multiple backend support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.embedding_provider = None
        self.vector_store = None
        self.fallback_store = None
        
        # Initialize embedding provider
        if config.get('vertex_ai'):
            self.embedding_provider = VertexAIEmbeddingProvider(
                project_id=config['vertex_ai']['project_id'],
                region=config['vertex_ai'].get('region', 'us-central1')
            )
        
        # Initialize vector store
        store_type = config.get('store_type', 'faiss')
        
        if store_type == 'pinecone' and config.get('pinecone'):
            self.vector_store = PineconeVectorStore(
                api_key=config['pinecone']['api_key'],
                environment=config['pinecone']['environment'],
                index_name=config['pinecone']['index_name'],
                dimension=config.get('dimension', 768)
            )
        else:
            # Default to FAISS
            self.vector_store = FAISSVectorStore(
                dimension=config.get('dimension', 768),
                index_type=config.get('faiss_index_type', 'IVF')
            )
        
        # Always have FAISS as fallback
        if not isinstance(self.vector_store, FAISSVectorStore):
            self.fallback_store = FAISSVectorStore(dimension=config.get('dimension', 768))
    
    async def add_documents(self, contents: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """Add documents with automatic embedding generation"""
        if not contents:
            return []
        
        # Generate embeddings
        if self.embedding_provider:
            embeddings = await self.embedding_provider.generate_embeddings(contents)
        else:
            # Use dummy embeddings for testing
            import random
            dimension = self.config.get('dimension', 768)
            embeddings = [[random.random() for _ in range(dimension)] for _ in contents]
        
        # Create VectorDocument objects
        documents = []
        doc_ids = []
        
        for i, (content, metadata, embedding) in enumerate(zip(contents, metadatas, embeddings)):
            doc_id = f"doc_{hash(content)}"
            doc_ids.append(doc_id)
            
            doc = VectorDocument(
                id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata,
                timestamp=datetime.now(),
                source=metadata.get('source', ''),
                service=metadata.get('service', ''),
                category=metadata.get('category', '')
            )
            documents.append(doc)
        
        # Store in primary store
        await self.vector_store.add_documents(documents)
        
        # Store in fallback if available
        if self.fallback_store:
            await self.fallback_store.add_documents(documents)
        
        return doc_ids
    
    async def search(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for similar documents"""
        # Generate query embedding
        if self.embedding_provider:
            query_embedding = await self.embedding_provider.generate_embedding(query)
        else:
            # Use dummy embedding for testing
            import random
            dimension = self.config.get('dimension', 768)
            query_embedding = [random.random() for _ in range(dimension)]
        
        # Search primary store
        try:
            results = await self.vector_store.search(query_embedding, k, filters)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Primary store search failed: {e}")
        
        # Fallback to secondary store
        if self.fallback_store:
            try:
                return await self.fallback_store.search(query_embedding, k, filters)
            except Exception as e:
                logger.error(f"Fallback store search failed: {e}")
        
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            'config': self.config,
            'embedding_provider': type(self.embedding_provider).__name__ if self.embedding_provider else None,
            'primary_store': type(self.vector_store).__name__ if self.vector_store else None,
            'has_fallback': self.fallback_store is not None
        }
        
        if hasattr(self.vector_store, 'get_stats'):
            stats['primary_stats'] = self.vector_store.get_stats()
        
        if self.fallback_store and hasattr(self.fallback_store, 'get_stats'):
            stats['fallback_stats'] = self.fallback_store.get_stats()
        
        return stats
    
    def save_to_disk(self, path: str) -> None:
        """Save vector store to disk"""
        if hasattr(self.vector_store, 'save_to_disk'):
            self.vector_store.save_to_disk(f"{path}_primary")
        
        if self.fallback_store and hasattr(self.fallback_store, 'save_to_disk'):
            self.fallback_store.save_to_disk(f"{path}_fallback")
    
    def load_from_disk(self, path: str) -> None:
        """Load vector store from disk"""
        if hasattr(self.vector_store, 'load_from_disk'):
            self.vector_store.load_from_disk(f"{path}_primary")
        
        if self.fallback_store and hasattr(self.fallback_store, 'load_from_disk'):
            self.fallback_store.load_from_disk(f"{path}_fallback")

# Factory function
def create_vector_store(config: Dict[str, Any]) -> EnterpriseVectorStore:
    """Create an enterprise vector store with the given configuration"""
    return EnterpriseVectorStore(config)