#!/bin/bash

# Knowledge Base and RAG System entrypoint script

set -e

echo "🧠 Starting Gemini Knowledge Base and RAG System..."

# Create necessary directories
mkdir -p /app/logs /app/data/documents /app/data/embeddings /app/data/indices /app/cache

# Set environment variables with defaults
export PYTHONPATH=/app
export PORT=${PORT:-8001}
export LOG_LEVEL=${LOG_LEVEL:-info}
export KNOWLEDGE_ENV=${KNOWLEDGE_ENV:-production}

# Vector database configuration
export VECTOR_DB_HOST=${VECTOR_DB_HOST:-localhost}
export VECTOR_DB_PORT=${VECTOR_DB_PORT:-6333}
export VECTOR_DB_TYPE=${VECTOR_DB_TYPE:-qdrant}

# Redis configuration for caching
export REDIS_HOST=${REDIS_HOST:-localhost}
export REDIS_PORT=${REDIS_PORT:-6379}

# Embedding model configuration
export EMBEDDING_MODEL=${EMBEDDING_MODEL:-all-MiniLM-L6-v2}
export CHUNK_SIZE=${CHUNK_SIZE:-512}
export CHUNK_OVERLAP=${CHUNK_OVERLAP:-50}
export MAX_TOKENS=${MAX_TOKENS:-4096}

echo "📊 Configuration:"
echo "  Port: $PORT"
echo "  Vector DB: $VECTOR_DB_TYPE at $VECTOR_DB_HOST:$VECTOR_DB_PORT"
echo "  Redis: $REDIS_HOST:$REDIS_PORT"
echo "  Embedding Model: $EMBEDDING_MODEL"
echo "  Chunk Size: $CHUNK_SIZE"

# Wait for dependencies
echo "⏳ Waiting for dependencies..."

# Wait for vector database
timeout=30
while ! nc -z $VECTOR_DB_HOST $VECTOR_DB_PORT; do
    if [ $timeout -le 0 ]; then
        echo "❌ Vector database not available at $VECTOR_DB_HOST:$VECTOR_DB_PORT"
        echo "⚠️  Continuing without vector database connection..."
        break
    fi
    echo "Waiting for vector database... ($timeout seconds remaining)"
    sleep 1
    timeout=$((timeout - 1))
done

# Wait for Redis
timeout=30
while ! nc -z $REDIS_HOST $REDIS_PORT; do
    if [ $timeout -le 0 ]; then
        echo "❌ Redis not available at $REDIS_HOST:$REDIS_PORT"
        echo "⚠️  Continuing without Redis connection..."
        break
    fi
    echo "Waiting for Redis... ($timeout seconds remaining)"
    sleep 1
    timeout=$((timeout - 1))
done

echo "✅ Dependencies check completed"

# Initialize knowledge base if needed
echo "🔄 Initializing knowledge base..."
python -c "
try:
    from src.knowledge.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()
    kb.initialize()
    print('✅ Knowledge base initialized successfully')
except Exception as e:
    print(f'⚠️  Knowledge base initialization warning: {e}')
"

# Start the knowledge base service
case "${1:-server}" in
    "server"|"start")
        echo "🚀 Starting Knowledge Base API server..."
        exec uvicorn src.api.rag_endpoints:app \
            --host 0.0.0.0 \
            --port $PORT \
            --workers 2 \
            --log-level $LOG_LEVEL
        ;;
    "index")
        echo "📚 Starting document indexing..."
        exec python -m src.knowledge.indexer
        ;;
    "interactive"|"bash")
        echo "🔧 Starting interactive shell..."
        exec /bin/bash
        ;;
    *)
        echo "🔧 Executing custom command: $*"
        exec "$@"
        ;;
esac