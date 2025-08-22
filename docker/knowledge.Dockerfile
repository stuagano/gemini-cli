# Knowledge Base Container for Gemini Enterprise RAG System
# Includes vector database connectivity and embedding models

# Build arguments
ARG PYTHON_VERSION=3.11

# Container metadata labels
LABEL maintainer="Gemini Enterprise Team"
LABEL description="Gemini Enterprise Knowledge Base and RAG System"
LABEL version="1.0.0"
LABEL build-date=""
LABEL vcs-url="https://github.com/google-gemini/gemini-cli"

# Stage 1: Build environment
FROM python:${PYTHON_VERSION}-slim as builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install additional RAG-specific dependencies
RUN pip install --no-cache-dir \
    # Vector databases
    chromadb==0.4.15 \
    qdrant-client==1.6.4 \
    weaviate-client==3.25.3 \
    # Embedding models
    sentence-transformers==2.2.2 \
    transformers==4.35.2 \
    torch==2.1.1 \
    # Text processing
    langchain==0.0.335 \
    tiktoken==0.5.1 \
    pypdf==3.17.0 \
    python-docx==0.8.11 \
    # Search and indexing
    rank-bm25==0.2.2 \
    elasticsearch==8.11.0

# Stage 2: Production image
FROM python:${PYTHON_VERSION}-slim as production

# Security labels
LABEL security.scan="enabled"
LABEL security.non-root="true"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8001 \
    KNOWLEDGE_ENV=production \
    VECTOR_DB_HOST=localhost \
    VECTOR_DB_PORT=6333 \
    REDIS_HOST=localhost \
    REDIS_PORT=6379 \
    EMBEDDING_MODEL=all-MiniLM-L6-v2 \
    CHUNK_SIZE=512 \
    CHUNK_OVERLAP=50 \
    MAX_TOKENS=4096

# Create non-root user
RUN groupadd -r -g 1000 knowledge && \
    useradd -r -u 1000 -g knowledge -m -s /bin/bash knowledge

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    ca-certificates \
    tini \
    # For document processing
    poppler-utils \
    tesseract-ocr \
    # For embedding models
    libgomp1 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy knowledge base source code
COPY src/knowledge/ ./src/knowledge/
COPY src/api/rag_endpoints.py ./src/api/
COPY src/models/ ./src/models/
COPY requirements.txt ./

# Create necessary directories
RUN mkdir -p /app/data/documents \
             /app/data/embeddings \
             /app/data/indices \
             /app/logs \
             /app/cache \
             /app/models && \
    chmod 755 /app/data /app/logs /app/cache /app/models

# Copy knowledge base startup script
COPY docker/scripts/knowledge-entrypoint.sh ./
RUN chmod +x knowledge-entrypoint.sh

# Set ownership to non-root user
RUN chown -R knowledge:knowledge /app

# Switch to non-root user
USER knowledge

# Download default embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/v1/knowledge/health || exit 1

# Signal handling for graceful shutdown
STOPSIGNAL SIGTERM

# Expose port
EXPOSE $PORT

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command
CMD ["./knowledge-entrypoint.sh"]