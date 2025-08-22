# Multi-stage Docker build for the Gemini Enterprise Architect Agent Server
# Optimized for production deployment with enhanced caching, security, and monitoring

# Build arguments for flexibility
ARG PYTHON_VERSION=3.11
ARG NODE_VERSION=20

# Container metadata labels
LABEL maintainer="Gemini Enterprise Team"
LABEL description="Gemini Enterprise Architect Agent Server"
LABEL version="1.0.0"
LABEL build-date=""
LABEL vcs-url="https://github.com/google-gemini/gemini-cli"

# Stage 1: Python dependencies and base
FROM python:${PYTHON_VERSION}-slim as python-base

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies for Python packages with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python dependency files first for better layer caching
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Node.js dependencies
FROM node:${NODE_VERSION}-slim as node-builder

# Set working directory
WORKDIR /app

# Copy package files for better caching
COPY package.json package-lock.json ./
COPY packages/cli/package.json ./packages/cli/
COPY packages/core/package.json ./packages/core/
COPY packages/test-utils/package.json ./packages/test-utils/

# Install Node.js dependencies
RUN npm ci --workspaces --prefer-offline --no-audit

# Copy source files
COPY . .

# Build TypeScript packages
RUN npm run build:packages

# Stage 3: Production image
FROM python:${PYTHON_VERSION}-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=info \
    APP_ENV=production \
    GRACEFUL_TIMEOUT=120 \
    KEEP_ALIVE=5 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=100

# Security labels
LABEL security.scan="enabled"
LABEL security.non-root="true"

# Create non-root user with specific UID/GID for security
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser -m -s /bin/bash appuser

# Install minimal runtime dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    ca-certificates \
    tini \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python dependencies from first stage
COPY --from=python-base /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Copy built Node.js packages (for CLI integration)
COPY --from=node-builder /app/packages/cli/dist ./packages/cli/dist/
COPY --from=node-builder /app/packages/core/dist ./packages/core/dist/
COPY --from=node-builder /app/packages/test-utils/dist ./packages/test-utils/dist/

# Copy Python source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY requirements.txt pytest.ini start_server.sh ./

# Copy configuration files
COPY .bmad-core/ ./.bmad-core/ 2>/dev/null || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/cache /app/tmp /home/appuser/.cache && \
    chmod 755 /app/logs /app/data /app/cache /app/tmp

# Copy startup script and make it executable
COPY start_server.sh ./
RUN chmod +x start_server.sh

# Set ownership to non-root user
RUN chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Health check with improved endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/v1/health || exit 1

# Signal handling for graceful shutdown
STOPSIGNAL SIGTERM

# Expose port
EXPOSE $PORT

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command with proper signal handling and worker configuration
CMD ["python", "src/start_server.py"]