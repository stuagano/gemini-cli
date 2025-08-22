#!/usr/bin/env python3
"""
Initialize and manage the RAG (Retrieval-Augmented Generation) database
This script sets up the vector store, populates it with initial data, and provides management utilities
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.rag_system import EnterpriseRAGSystem, RAGQuery
from knowledge.vector_store import create_vector_store, VectorDocument
from knowledge.knowledge_base import EnterpriseKnowledgeBase, DocumentChunk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGInitializer:
    """Manages RAG system initialization and data loading"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.config = self.load_config(config_path)
        self.rag_system = None
        self.vector_store = None
        self.knowledge_base = None
        
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        
        # Default configuration
        return {
            'project_id': os.environ.get('GCP_PROJECT_ID', 'gemini-enterprise-architect'),
            'region': os.environ.get('GCP_REGION', 'us-central1'),
            'vector_store': {
                'store_type': 'faiss',  # faiss or pinecone
                'dimension': 768,
                'faiss_index_type': 'IVF',
                'persist_path': str(self.data_dir / 'vector_store')
            },
            'vertex_ai': {
                'project_id': os.environ.get('GCP_PROJECT_ID', 'gemini-enterprise-architect'),
                'region': os.environ.get('GCP_REGION', 'us-central1')
            }
        }
    
    async def initialize_system(self) -> None:
        """Initialize the RAG system components"""
        logger.info("Initializing RAG system...")
        
        # Initialize RAG system
        self.rag_system = EnterpriseRAGSystem(
            project_id=self.config['project_id'],
            region=self.config['region']
        )
        
        # Initialize vector store
        self.vector_store = create_vector_store(self.config['vector_store'])
        
        # Initialize knowledge base
        self.knowledge_base = EnterpriseKnowledgeBase(
            project_id=self.config['project_id'],
            region=self.config['region']
        )
        
        await self.rag_system.initialize(self.config['vector_store'])
        await self.knowledge_base.initialize()
        
        logger.info("RAG system initialized successfully")
    
    async def load_initial_data(self) -> None:
        """Load initial documentation and knowledge"""
        logger.info("Loading initial data...")
        
        # Load GCP service documentation
        await self.load_gcp_docs()
        
        # Load BMAD methodology documents
        await self.load_bmad_docs()
        
        # Load architecture patterns
        await self.load_architecture_patterns()
        
        # Load code examples
        await self.load_code_examples()
        
        logger.info("Initial data loading complete")
    
    async def load_gcp_docs(self) -> None:
        """Load GCP service documentation"""
        logger.info("Loading GCP documentation...")
        
        gcp_services = [
            {
                'service': 'Cloud Run',
                'category': 'compute',
                'content': """Cloud Run is a managed compute platform that automatically scales stateless containers.
                Key features:
                - Fully managed serverless platform
                - Automatic scaling from zero to thousands
                - Pay only for resources used
                - Built on Knative and Kubernetes
                - Supports any language, library, or binary
                
                Use cases:
                - Web applications and APIs
                - Microservices
                - Event-driven processing
                - Batch jobs
                
                Best practices:
                - Use Cloud Build for CI/CD
                - Implement graceful shutdown
                - Set appropriate CPU and memory limits
                - Use Secret Manager for sensitive data
                - Enable Cloud Trace for distributed tracing""",
                'url': 'https://cloud.google.com/run/docs'
            },
            {
                'service': 'BigQuery',
                'category': 'analytics',
                'content': """BigQuery is Google's serverless, highly scalable enterprise data warehouse.
                Key features:
                - Serverless architecture with automatic scaling
                - Real-time analytics with streaming inserts
                - Built-in machine learning with BigQuery ML
                - Geospatial analysis
                - Data encryption at rest and in transit
                
                Use cases:
                - Business intelligence and reporting
                - Real-time analytics
                - Predictive analytics
                - Log analysis
                - IoT data processing
                
                Best practices:
                - Partition tables by date for cost optimization
                - Use clustering for improved query performance
                - Implement slot reservations for predictable pricing
                - Use materialized views for frequently accessed data
                - Enable query caching""",
                'url': 'https://cloud.google.com/bigquery/docs'
            },
            {
                'service': 'Vertex AI',
                'category': 'ai',
                'content': """Vertex AI is Google's unified ML platform for building, deploying, and scaling ML models.
                Key features:
                - AutoML for code-free model training
                - Custom training with any framework
                - Model deployment and serving
                - Feature store for ML features
                - Model monitoring and explainability
                
                Use cases:
                - Computer vision applications
                - Natural language processing
                - Recommendation systems
                - Time series forecasting
                - Fraud detection
                
                Best practices:
                - Use Feature Store for feature consistency
                - Implement model versioning
                - Set up continuous evaluation
                - Use Vertex AI Pipelines for MLOps
                - Monitor model drift and performance""",
                'url': 'https://cloud.google.com/vertex-ai/docs'
            },
            {
                'service': 'Cloud Spanner',
                'category': 'database',
                'content': """Cloud Spanner is a globally distributed, strongly consistent database service.
                Key features:
                - Horizontal scaling with strong consistency
                - 99.999% availability SLA
                - Automatic replication
                - ACID transactions
                - SQL support
                
                Use cases:
                - Global applications requiring consistency
                - Financial services and trading
                - Gaming leaderboards
                - Supply chain management
                - Inventory systems
                
                Best practices:
                - Design schema for horizontal scaling
                - Use interleaved tables for related data
                - Implement stale reads for better performance
                - Monitor and optimize query performance
                - Use batch operations for bulk updates""",
                'url': 'https://cloud.google.com/spanner/docs'
            }
        ]
        
        # Add documents to vector store
        documents = []
        for service_doc in gcp_services:
            doc = VectorDocument(
                id=f"gcp_{service_doc['service'].lower().replace(' ', '_')}",
                content=service_doc['content'],
                embedding=[],  # Will be generated by vector store
                metadata={
                    'source': 'gcp_docs',
                    'last_updated': datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                source=service_doc['url'],
                service=service_doc['service'],
                category=service_doc['category']
            )
            documents.append(doc)
        
        # Generate embeddings and store
        if self.vector_store:
            contents = [doc.content for doc in documents]
            metadatas = [
                {
                    'service': doc.service,
                    'category': doc.category,
                    'source': doc.source
                }
                for doc in documents
            ]
            
            await self.vector_store.add_documents(contents, metadatas)
            logger.info(f"Added {len(documents)} GCP documentation entries")
    
    async def load_bmad_docs(self) -> None:
        """Load BMAD methodology documentation"""
        logger.info("Loading BMAD documentation...")
        
        bmad_docs = [
            {
                'title': 'BMAD Core Principles',
                'category': 'methodology',
                'content': """BMAD (Breakthrough Method for Agile AI-Driven Development) core principles:
                
                1. Scout-First Development:
                - Always analyze existing codebase before creating new code
                - Identify patterns and reusable components
                - Prevent duplication and technical debt
                
                2. Continuous Validation:
                - Real-time code validation during development
                - Immediate feedback on issues
                - Proactive problem prevention
                
                3. Multi-Agent Orchestration:
                - Specialized agents for different tasks
                - Collaborative problem solving
                - Context-aware agent selection
                
                4. Value Stream Optimization:
                - Focus on end-to-end value delivery
                - Eliminate waste at every stage
                - Continuous improvement cycles
                
                5. Enterprise-Ready Architecture:
                - Scalable from day one
                - Security and compliance built-in
                - Production-ready deployments""",
                'service': 'BMAD',
                'url': 'internal://bmad/principles'
            },
            {
                'title': 'Agent Capabilities',
                'category': 'agents',
                'content': """BMAD Agent System Capabilities:
                
                Analyst Agent (Mary):
                - Market research and competitive analysis
                - Requirements gathering and analysis
                - Feasibility studies
                - Business case development
                
                PM Agent (Product Manager):
                - Product roadmap planning
                - User story creation
                - Sprint planning
                - Stakeholder communication
                
                Architect Agent:
                - System design and architecture
                - Technology selection
                - Scalability planning
                - Security architecture
                
                Developer Agent:
                - Code generation
                - Implementation of features
                - Code optimization
                - Documentation
                
                QA Agent:
                - Test planning and execution
                - Quality assurance
                - Performance testing
                - Security testing
                
                Scout Agent:
                - Code duplication detection
                - Pattern recognition
                - Dependency analysis
                - Technical debt identification
                
                PO Agent (Product Owner):
                - Value prioritization
                - Release planning
                - Stakeholder management
                - ROI analysis""",
                'service': 'BMAD',
                'url': 'internal://bmad/agents'
            }
        ]
        
        # Add BMAD documents
        documents = []
        for bmad_doc in bmad_docs:
            doc = VectorDocument(
                id=f"bmad_{bmad_doc['title'].lower().replace(' ', '_')}",
                content=bmad_doc['content'],
                embedding=[],
                metadata={
                    'source': 'bmad_docs',
                    'last_updated': datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                source=bmad_doc['url'],
                service=bmad_doc['service'],
                category=bmad_doc['category']
            )
            documents.append(doc)
        
        if self.vector_store:
            contents = [doc.content for doc in documents]
            metadatas = [
                {
                    'service': doc.service,
                    'category': doc.category,
                    'source': doc.source
                }
                for doc in documents
            ]
            
            await self.vector_store.add_documents(contents, metadatas)
            logger.info(f"Added {len(documents)} BMAD documentation entries")
    
    async def load_architecture_patterns(self) -> None:
        """Load architecture patterns and best practices"""
        logger.info("Loading architecture patterns...")
        
        patterns = [
            {
                'name': 'Microservices on GKE',
                'category': 'architecture',
                'content': """Microservices Architecture on Google Kubernetes Engine (GKE):
                
                Pattern Overview:
                - Decompose applications into small, independent services
                - Each service owns its data and business logic
                - Services communicate via APIs
                
                GCP Services:
                - GKE for container orchestration
                - Cloud Load Balancing for traffic distribution
                - Cloud Armor for DDoS protection
                - Anthos Service Mesh for service management
                
                Implementation:
                1. Design service boundaries around business capabilities
                2. Implement API contracts using OpenAPI
                3. Use Cloud Build for CI/CD pipelines
                4. Deploy with Kubernetes manifests or Helm charts
                5. Implement observability with Cloud Monitoring
                
                Best Practices:
                - One service per repository
                - Implement circuit breakers
                - Use distributed tracing
                - Implement proper retry logic
                - Design for failure""",
                'url': 'https://cloud.google.com/architecture/microservices-architecture-gke'
            },
            {
                'name': 'Event-Driven Architecture',
                'category': 'architecture',
                'content': """Event-Driven Architecture on GCP:
                
                Pattern Overview:
                - Loosely coupled components communicate via events
                - Asynchronous processing
                - Scalable and resilient
                
                GCP Services:
                - Pub/Sub for message queuing
                - Cloud Functions for event processing
                - Dataflow for stream processing
                - BigQuery for analytics
                
                Implementation:
                1. Define event schemas and contracts
                2. Set up Pub/Sub topics and subscriptions
                3. Implement Cloud Functions for event handlers
                4. Use Dataflow for complex event processing
                5. Store events in BigQuery for analysis
                
                Best Practices:
                - Implement idempotent operations
                - Use dead letter queues
                - Monitor message age and backlog
                - Implement event sourcing where appropriate
                - Version event schemas""",
                'url': 'https://cloud.google.com/architecture/event-driven-architecture'
            }
        ]
        
        # Add architecture patterns
        for pattern in patterns:
            await self.add_document(
                content=pattern['content'],
                metadata={
                    'title': pattern['name'],
                    'category': pattern['category'],
                    'source': pattern['url'],
                    'service': 'Architecture Patterns'
                }
            )
        
        logger.info(f"Added {len(patterns)} architecture patterns")
    
    async def load_code_examples(self) -> None:
        """Load code examples and snippets"""
        logger.info("Loading code examples...")
        
        examples = [
            {
                'title': 'Cloud Run FastAPI Deployment',
                'language': 'python',
                'content': """Deploying FastAPI on Cloud Run:

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="Gemini API", version="1.0.0")

class HealthCheck(BaseModel):
    status: str
    service: str
    version: str

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        service="gemini-api",
        version=os.environ.get("VERSION", "1.0.0")
    )

@app.get("/")
async def root():
    return {"message": "Gemini Enterprise Architect API"}

# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# Deploy command
# gcloud run deploy gemini-api \\
#   --source . \\
#   --region us-central1 \\
#   --allow-unauthenticated
```""",
                'category': 'code'
            },
            {
                'title': 'BigQuery Python Client',
                'language': 'python',
                'content': """Using BigQuery Python Client:

```python
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import pandas as pd

class BigQueryClient:
    def __init__(self, project_id: str):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
    
    def run_query(self, query: str) -> pd.DataFrame:
        \"\"\"Execute a query and return results as DataFrame\"\"\"
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return results.to_dataframe()
        except GoogleCloudError as e:
            raise Exception(f"Query failed: {e}")
    
    def stream_insert(self, dataset_id: str, table_id: str, rows: List[Dict]):
        \"\"\"Stream insert rows into BigQuery table\"\"\"
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)
        
        errors = self.client.insert_rows_json(table, rows)
        if errors:
            raise Exception(f"Insert failed: {errors}")
        
        return len(rows)
    
    def create_dataset(self, dataset_id: str, location: str = "US"):
        \"\"\"Create a new dataset\"\"\"
        dataset = bigquery.Dataset(f"{self.project_id}.{dataset_id}")
        dataset.location = location
        
        dataset = self.client.create_dataset(dataset, exists_ok=True)
        return dataset

# Usage example
client = BigQueryClient("my-project")
df = client.run_query("SELECT * FROM `project.dataset.table` LIMIT 10")
```""",
                'category': 'code'
            }
        ]
        
        # Add code examples
        for example in examples:
            await self.add_document(
                content=example['content'],
                metadata={
                    'title': example['title'],
                    'language': example.get('language', 'python'),
                    'category': example['category'],
                    'service': 'Code Examples'
                }
            )
        
        logger.info(f"Added {len(examples)} code examples")
    
    async def add_document(self, content: str, metadata: Dict[str, Any]) -> None:
        """Add a single document to the vector store"""
        if self.vector_store:
            await self.vector_store.add_documents([content], [metadata])
    
    async def test_rag_system(self) -> None:
        """Test the RAG system with sample queries"""
        logger.info("Testing RAG system...")
        
        test_queries = [
            "How do I deploy a FastAPI application on Cloud Run?",
            "What are the best practices for using BigQuery?",
            "Explain the BMAD Scout-first architecture",
            "How do I implement microservices on GKE?",
            "What is Vertex AI and when should I use it?"
        ]
        
        for query_text in test_queries:
            logger.info(f"\nTesting query: {query_text}")
            
            query = RAGQuery(
                query=query_text,
                query_type="general",
                max_context_chunks=3,
                temperature=0.3
            )
            
            try:
                response = await self.rag_system.query(query)
                logger.info(f"Response confidence: {response.confidence}")
                logger.info(f"Response preview: {response.answer[:200]}...")
                logger.info(f"Sources: {len(response.sources)} documents found")
            except Exception as e:
                logger.error(f"Query failed: {e}")
    
    async def save_vector_store(self) -> None:
        """Save vector store to disk"""
        if self.vector_store:
            save_path = self.data_dir / "vector_store"
            self.vector_store.save_to_disk(str(save_path))
            logger.info(f"Vector store saved to {save_path}")
    
    async def load_vector_store(self) -> None:
        """Load vector store from disk"""
        if self.vector_store:
            load_path = self.data_dir / "vector_store"
            if load_path.exists():
                self.vector_store.load_from_disk(str(load_path))
                logger.info(f"Vector store loaded from {load_path}")
            else:
                logger.warning(f"No saved vector store found at {load_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        stats = {}
        
        if self.rag_system:
            stats['rag_system'] = self.rag_system.get_system_stats()
        
        if self.vector_store:
            stats['vector_store'] = self.vector_store.get_stats()
        
        return stats

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Initialize and manage RAG database')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--init', action='store_true', help='Initialize RAG system')
    parser.add_argument('--load-data', action='store_true', help='Load initial data')
    parser.add_argument('--test', action='store_true', help='Test RAG system')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--save', action='store_true', help='Save vector store to disk')
    parser.add_argument('--load', action='store_true', help='Load vector store from disk')
    
    args = parser.parse_args()
    
    # Create initializer
    initializer = RAGInitializer(args.config)
    
    try:
        # Initialize system if requested
        if args.init:
            await initializer.initialize_system()
            logger.info("RAG system initialized")
        
        # Load existing vector store if available
        if args.load:
            await initializer.initialize_system()
            await initializer.load_vector_store()
        
        # Load data if requested
        if args.load_data:
            if not initializer.rag_system:
                await initializer.initialize_system()
            await initializer.load_initial_data()
            await initializer.save_vector_store()
        
        # Test system if requested
        if args.test:
            if not initializer.rag_system:
                await initializer.initialize_system()
                await initializer.load_vector_store()
            await initializer.test_rag_system()
        
        # Show statistics if requested
        if args.stats:
            if not initializer.rag_system:
                await initializer.initialize_system()
                await initializer.load_vector_store()
            stats = initializer.get_statistics()
            print("\nRAG System Statistics:")
            print(json.dumps(stats, indent=2, default=str))
        
        # Save vector store if requested
        if args.save:
            await initializer.save_vector_store()
        
        # Default action if no flags provided
        if not any([args.init, args.load_data, args.test, args.stats, args.save, args.load]):
            logger.info("No action specified. Use --help for options.")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())