# RAG (Retrieval-Augmented Generation) System

The RAG system provides intelligent knowledge retrieval and response generation for the Gemini Enterprise Architect. It combines vector similarity search with LLM-powered response generation to answer questions about GCP services, BMAD methodology, and your codebase.

## Components

### 1. Core RAG System (`rag_system.py`)
- Main orchestrator for knowledge retrieval and response generation
- Integrates with Vertex AI for embeddings and generation
- Supports different query types (general, code, architecture, troubleshooting)
- Response caching for performance

### 2. Vector Store (`vector_store.py`)
- FAISS-based local vector store for fast similarity search
- Optional Pinecone integration for cloud storage
- Vertex AI embeddings generation
- Persistent storage to disk

### 3. Knowledge Base (`knowledge_base.py`)
- GCP documentation management
- Service recommendation engine
- Document chunking and processing

### 4. RAG API Endpoints (`rag_endpoints.py`)
- FastAPI endpoints for querying the knowledge base
- Document management APIs
- Health checks and statistics

### 5. Document Ingestion Pipeline (`document_ingestion.py`)
- Continuous monitoring of directories for new documents
- Support for multiple file formats (Markdown, Python, JSON, YAML, etc.)
- Automatic chunking and embedding generation
- Batch processing for efficiency

### 6. RAG Initializer (`initialize_rag.py`)
- System initialization and configuration
- Initial data loading
- Testing utilities

## Setup

### Prerequisites

```bash
# Install required packages
pip install faiss-cpu  # or faiss-gpu if you have CUDA
pip install vertexai
pip install google-cloud-aiplatform
pip install markdown
pip install beautifulsoup4
pip install watchdog
pip install redis
pip install ratelimit
```

### Configuration

1. Set environment variables:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

2. Create a configuration file (optional):
```yaml
# rag_config.yaml
project_id: gemini-enterprise-architect
region: us-central1
vector_store:
  store_type: faiss
  dimension: 768
  persist_path: ./data/vector_store
vertex_ai:
  project_id: gemini-enterprise-architect
  region: us-central1
```

## Usage

### Initialize and Load Data

```bash
# Initialize the RAG system
python src/knowledge/initialize_rag.py --init

# Load initial data (GCP docs, BMAD docs, examples)
python src/knowledge/initialize_rag.py --load-data

# Or do both at once
python src/knowledge/initialize_rag.py --init --load-data
```

### Test the System

```bash
# Run test queries
python src/knowledge/test_rag.py

# Or test with the initializer
python src/knowledge/initialize_rag.py --test
```

### Start Document Ingestion

```bash
# Watch directories for new documents
python src/knowledge/document_ingestion.py --watch ./docs ./src

# Run as daemon (continuous monitoring)
python src/knowledge/document_ingestion.py --daemon --watch ./docs ./src
```

### Query via API

Start the agent server with RAG endpoints:
```bash
python src/api/agent_server.py
```

Then query the API:
```bash
# Query the knowledge base
curl -X POST http://localhost:8000/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I deploy on Cloud Run?",
    "query_type": "general",
    "max_results": 5
  }'

# Search documents
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "BigQuery optimization",
    "limit": 10
  }'

# Get statistics
curl http://localhost:8000/api/v1/knowledge/stats
```

### Python Integration

```python
from knowledge.initialize_rag import RAGInitializer
from knowledge.rag_system import RAGQuery

async def query_knowledge():
    # Initialize
    initializer = RAGInitializer()
    await initializer.initialize_system()
    
    # Load existing vector store
    await initializer.load_vector_store()
    
    # Create query
    query = RAGQuery(
        query="What are Cloud Run best practices?",
        query_type="architecture",
        max_context_chunks=5,
        temperature=0.3
    )
    
    # Get response
    response = await initializer.rag_system.query(query)
    
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}")
    print(f"Sources: {len(response.sources)}")
```

## File Formats Supported

The document ingestion pipeline supports:
- **Markdown** (`.md`) - Structured documentation
- **Python** (`.py`) - Extracts classes, functions, docstrings
- **JavaScript/TypeScript** (`.js`, `.ts`) - Code files
- **YAML** (`.yaml`, `.yml`) - Configuration files
- **JSON** (`.json`) - Data files
- **HTML** (`.html`) - Web pages
- **Text** (`.txt`) - Plain text

## Performance Optimization

### Caching
- Response caching with Redis (if available)
- In-memory caching with TTL
- Vector store persistence to disk

### Batch Processing
- Document ingestion in batches
- Embedding generation in batches
- Configurable batch size and timeout

### Vector Search
- FAISS IVF index for large datasets
- Flat index for small datasets
- Configurable similarity threshold

## Monitoring

### Statistics
```bash
# Get system statistics
python src/knowledge/initialize_rag.py --stats
```

### Metrics Available
- Total documents in vector store
- Index size and type
- Cache hit rate
- Average query time
- Processing queue size
- Error counts

## Troubleshooting

### Common Issues

1. **Vertex AI not available**
   - System will use fallback responses
   - Check GCP credentials and project setup

2. **FAISS not installed**
   - Install with: `pip install faiss-cpu`
   - System will use fallback similarity search

3. **Redis connection failed**
   - Caching will be disabled
   - Install and start Redis: `redis-server`

4. **Large files causing memory issues**
   - Adjust `max_document_size` in configuration
   - Reduce `chunk_size` for smaller chunks

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   User Query    │────▶│  RAG System  │────▶│   Response  │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌──────────────┐     ┌──────────────┐
            │ Vector Store │     │ Knowledge    │
            │   (FAISS)    │     │    Base      │
            └──────────────┘     └──────────────┘
                    │                     │
                    ▼                     ▼
            ┌──────────────┐     ┌──────────────┐
            │  Embeddings  │     │  Documents   │
            │ (Vertex AI)  │     │   (GCP,etc)  │
            └──────────────┘     └──────────────┘
```

## Next Steps

1. **Production Deployment**
   - Set up Vertex AI in GCP
   - Configure service accounts
   - Deploy to Cloud Run

2. **Enhanced Features**
   - Add more document sources
   - Implement feedback loop
   - Add user personalization

3. **Performance Tuning**
   - Optimize embedding dimensions
   - Fine-tune similarity thresholds
   - Implement query optimization

## Contributing

When adding new features:
1. Update document processors for new file types
2. Add test cases to `test_rag.py`
3. Update this README
4. Test with sample data

## License

Part of the Gemini Enterprise Architect project.